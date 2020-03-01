<?php
header("Content-Type: application/json; charset=UTF-8");

$Cached = null;

function GetAgent($fallback = "PSO2es Tweaker 1.1") : string
{
	$tag = " (GitHub; alama)";
	if ($_SERVER)
	{
		if (array_key_exists("HTTP_USER_AGENT", $_SERVER))
		{
			return $_SERVER['HTTP_USER_AGENT'] + $tag;
		}
	}
	return $fallback + $tag;
}

function BuildRESTURL($Settings = null) : string
{
	if (is_null($Settings))
	{
		$Settings = $GLOBALS['DefaultSettings'];
	}

	$url_base = "https://api.github.com/repos/:owner/:repos/releases/latest";

	$url = str_replace(array_keys($Settings), $Settings, $url_base);

	return $url;
}

function GetRESTData($url, $retry = 3) : string
{
	if ($retry == 0)
	{
		error_log("Could not download REST data");
		return "";
	}

	$httpopts = array(
	  'http'=>array(
		'method'=>"GET",
		'user_agent'=>GetAgent(),
		'header'=>"Accept: application/vnd.github.v3+json\r\n"
	  )
	);

	$httpheader = stream_context_create($httpopts);
	$contents = null;

	try
	{
		$contents = @file_get_contents($url, false, $httpheader);

		if ($contents === false)
		{ // Handle exception and retry
			return GetRESTData($url, ($retry - 1));
		}
	}
	catch (Exception $e)
	{ // Handle exception
		error_log($e);
		return "";
	}

	if (is_null($contents))
	{
		error_log("file_get_contents() is disabled");
		return "";
	}

	return $contents;
}

function GetRESTArray($Settings = null) : array
{
	if (is_null($Settings))
	{
		$Settings = $GLOBALS['DefaultSettings'];
	}

	$url = BuildRESTURL($Settings);

	$content = GetRESTData($url);

	if ($content == "")
	{
		return [];
	}

	$Data = json_decode($content, TRUE);

	if (is_null($Data))
	{
		error_log(json_list_error_msg());
		//json_last_error
		return [];

	}

	return $Data;
}

function GetPatchArray($Settings = null): array
{
	if (is_null($Settings))
	{
		$Settings = $GLOBALS['DefaultSettings'];
	}

	global $Cached;
	if (is_null($Cached))
	{
		$Data = GetRESTArray($Settings);
		$Cached = $Data;
	}
	else
	{
		$Data = $Cached;
	}

	if ($Data == [])
	{
		error_log("Can not fetch JSON");
		return [];
	}
	return $Data;
}

function GetPatchURL($Settings = null):  string
{
	if (is_null($Settings))
	{
		$Settings = $GLOBALS['DefaultSettings'];
	}

	$Data = GetPatchArray($Settings);

	if ($Data == [])
	{
		return "";
	}

	if (array_key_exists("assets", $Data))
	{
		$Data = $Data["assets"][0];
	}
	else
	{
		error_log("No assets in JSON entry");
		return "";
	}

	if (array_key_exists("browser_download_url", $Data))
	{
		return $Data["browser_download_url"];
	}

	error_log("No browser_download_url in JSON entry");

	return "";
}

function GetPatchVersion($Settings = null, $retry = 3) : string
{
	if (is_null($Settings))
	{
		$Settings = $GLOBALS['DefaultSettings'];
	}

	if ($retry == 0)
	{
		error_log("Could not download version file");
		return "";
	}

	$Data = GetPatchArray($Settings);

	if (array_key_exists("tag_name", $Data))
	{
		return $Data["tag_name"];
	}

	error_log("No tag_name in JSON entry");

	return "";
}

function MakePatchFeed($Settings = null) : string
{
	if (is_null($Settings))
	{
		$Settings = $GLOBALS['DefaultSettings'];
	}

	$Feed = $GLOBALS['DefaultFeed'];
	$version = GetPatchVersion($Settings);
	$url = GetPatchURL($Settings);
	$compatible = ($version != '' && $url != '');
	$message = str_replace(array_keys($Settings), $Settings, $Feed["patch_message"]);

	$Feed["patch_version"] = $version;
	$Feed["patch_url"] = $url;
	$Feed["patch_compatible"] = $compatible;
	$Feed["patch_message"] = $message;

	$Data = json_encode($Feed, JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES);

	$Data .= "\n";

	return $Data;
}

function CheckPOSTSettings($CGI = null) : array
{
	$Settings = $GLOBALS['DefaultSettings'];

	if (!is_null($CGI) and $CGI)
	{
		if (array_key_exists("owner", $CGI))
		{
			$Settings[":owner"] = $CGI["owner"];
		}

		if (array_key_exists("repos", $CGI))
		{
			$Settings[":repos"] = $CGI["repos"];
		}
	}

	return $Settings;
}

$DefaultSettings = Array
(
	":owner" => "SynthSy",
	":repos"=> "PSO2es-Translation",
);

$DefaultFeed = Array
(
	"patch_version" => "000",
	"patch_url" => "https://github.com/:owner/:repos/releases/download/:tag_name/patch.zip",
	"patch_compatible" => 1,
	"patch_message" => "GitHub: :owner/:repos build",
);

function main()
{
	$Settings = CheckPOSTSettings($_GET);
	print(MakePatchFeed($Settings));
}

main();
?>
