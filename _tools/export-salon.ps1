
$PSO2esPath = Join-Path -Path (Get-Location) -ChildPath "PSO2esTranslations"
$JSONPath = Join-Path -Path $PSO2esPath -ChildPath "json"
$PSO2ClassicPath = Join-Path -Path (Get-Location) -ChildPath "PSO2ENPatchCSV"

$FilterFiles_Chara = @(
"Item_Stack_Hairstyle.txt",
"Item_Stack_Headparts.txt",
"Item_Stack_Voice.txt",
"Item_Stack_FacePaint.txt",
"Item_Stack_EyeLash.txt",
"Item_Stack_EyeBrow.txt",
"Item_Stack_Eye.txt",
"Item_Stack_BodyPaint.txt",
"Item_Parts_LegMale.txt",
"Item_Parts_LegFemale.txt",
"Item_Parts_BodyMale.txt",
"Item_Parts_BodyFemale.txt",
"Item_Parts_ArmMale.txt",
"Item_Parts_ArmFemale.txt",
"Item_Outer_Male.txt",
"Item_Outer_Female.txt",
"Item_InnerWear_Male.txt",
"Item_InnerWear_Female.txt",
"Item_Costume_Male.txt",
"Item_Costume_Female.txt",
"Item_BaseWear_Male.txt",
"Item_BaseWear_Female.txt"
)

$JsonFiles_Chara = @()
Write-Host -Object ("Finding JSON files from {0}" -f $JSONPath)
$JsonFiles_Chara += Get-ChildItem -LiteralPath $JSONPath -Filter "*.txt" -File | Where-Object -Property Name -In -Value $FilterFiles_Chara
Write-Host -Object ("Found {1} JSON files from {0}" -f $JSONPath, $JsonFiles_Chara.Count)

$JsonData_Chara = @()
Write-Host -Object ("Loading JSON files from {0}" -f $JSONPath)
$JsonData_Chara += $JsonFiles_Chara | ForEach-Object -Process {
    $RAWDATA = $_ | Get-Content -Encoding UTF8 | ConvertFrom-Json
    $RAWDATA | Select-Object -Property jp_text, tr_text
} | Where-Object -Property tr_text -NE -Value ""
Write-Host -Object ("Loaded JSON files from {0}, found {1} entries" -f $JSONPath, $JsonData_Chara.Count)

Write-Host -Object ("Converting JSON {0} entries into a HashTable.." -f $JsonData_Chara.Count)
$JsonHT_Chara = $JsonData_Chara | Group-Object -Property jp_text -AsHashTable
Write-Host -Object ("Converted JSON entries into a HashTable of {0} entries.." -f $JsonHT_Chara.Count)

$JSONKeys_Chara = $JsonData_Chara.jp_text

$CharaPathFile = @()
Write-Host -Object ("Looking for ui_charamake_parts file from {0}" -f $PSO2ClassicPath)
$CharaPathFile += Get-ChildItem -LiteralPath $PSO2ClassicPath -Filter "ui_charamake_parts.csv" -Recurse -File
Write-Host -Object ("Found {1} ui_charamake_parts file from {0}" -f $PSO2ClassicPath, $CharaPathFile.Count)

$CharaPathFile | ForEach-Object -Process {
    $CSVFileItem = $_
    Write-Host -Object ("Loading CSV file: {0}" -f $CSVFileItem.FullName)
    $CsvData = Import-Csv -LiteralPath $CSVFileItem.FullName -Header @("ENTRY","TEXT") -Encoding UTF8
    Write-Host -Object ("Loaded CSV file: {0}" -f $CSVFileItem.FullName)
    $RawData = @()
    $RawData += $CsvData | ForEach-Object -Begin {
        Write-Host -Object ("Processing {0} lines for CSV file" -f $CsvData.Count)
    } -Process {
        $Key = ($_.TEXT.Substring(1,($_.TEXT.Length-2)) -replace '\\u3000','　').TrimEnd()
        If ($Key -in $JSONKeys_Chara)
        {
            $_.TEXT = '"{0}"' -f $JsonHT_Chara[$Key].tr_text
        }
        '{0},""{1}""' -f $_.ENTRY, $_.TEXT
    } -End {
        Write-Host -Object ("Processed {0} lines for CSV file" -f $CsvData.Count)
    } -Verbose
    Write-Host -Object ("Dumping {1} lines to {0}" -f $CSVFileItem.FullName, $RawData.Count)
    [System.IO.File]::WriteAllLines($CSVFileItem.FullName,$RawData)
    Write-Host -Object ("Dumped {1} lines to {0}" -f $CSVFileItem.FullName, $RawData.Count)
} -Verbose

Write-Host -Object "-------------------------------------------------------------------------------"

$FilterFiles_Accessories = @(
"Item_Stack_Accessory.txt",
" Name_UICharMake_AccessoryName.txt "
)

$JsonFiles = @()
Write-Host -Object ("Finding JSON files from {0}, for Accessories" -f $JSONPath)
$JsonFiles += Get-ChildItem -LiteralPath $JSONPath -Filter "*.txt" -File | Where-Object -Property Name -In -Value $FilterFiles_Accessories
Write-Host -Object ("Found {1} JSON files from {0}" -f $JSONPath, $JsonFiles.Count)

$JsonData = @()
Write-Host -Object ("Loading JSON files from {0}" -f $JSONPath)
$JsonData += $JsonFiles | ForEach-Object -Process {
    $RAWDATA = $_ | Get-Content -Encoding UTF8 | ConvertFrom-Json
    $RAWDATA | Select-Object -Property jp_text, tr_text
} | Where-Object -Property tr_text -NE -Value ""
Write-Host -Object ("Loaded JSON files from {0}, found {1} entries" -f $JSONPath, $JsonData.Count)

Write-Host -Object ("Converting JSON {0} entries into a HashTable.." -f $JsonData.Count)
$JsonHT = $JsonData | Group-Object -Property jp_text -AsHashTable
Write-Host -Object ("Converted JSON entries into a HashTable of {0} entries.." -f $JsonHT.Count)

$JSONKeys = $JsonData.jp_text

$AccessoriesPathFile = @()
Write-Host -Object ("Looking for ui_accessories_text file from {0}" -f $PSO2ClassicPath)
$AccessoriesPathFile += Get-ChildItem -LiteralPath $PSO2ClassicPath -Filter "ui_accessories_text.csv" -Recurse -File
Write-Host -Object ("Found {1} ui_accessories_text file from {0}" -f $PSO2ClassicPath, $AccessoriesPathFile.Count)

$AccessoriesPathFile | ForEach-Object -Process {
    $CSVFileItem = $_
    Write-Host -Object ("Loading CSV file: {0}" -f $CSVFileItem.FullName)
    $CsvData = Import-Csv -LiteralPath $CSVFileItem.FullName -Header @("ENTRY","TEXT") -Encoding UTF8
    Write-Host -Object ("Loaded CSV file: {0}" -f $CSVFileItem.FullName)
    $RawData = @()
    $RawData += $CsvData | ForEach-Object -Begin {
        Write-Host -Object ("Processing {0} lines for CSV file" -f $CsvData.Count)
    } -Process {
        $Key = ($_.TEXT.Substring(1,($_.TEXT.Length-2)) -replace '\\u3000','　').TrimEnd()
        If ($Key -in $JSONKeys)
        {
            $_.TEXT = '"{0}"' -f $JsonHT[$Key].tr_text
        }
        '{0},""{1}""' -f $_.ENTRY, $_.TEXT
    } -End {
        Write-Host -Object ("Processed {0} lines for CSV file" -f $CsvData.Count)
    } -Verbose
    Write-Host -Object ("Dumping {1} lines to {0}" -f $CSVFileItem.FullName, $RawData.Count)
    [System.IO.File]::WriteAllLines($CSVFileItem.FullName,$RawData)
    Write-Host -Object ("Dumped {1} lines to {0}" -f $CSVFileItem.FullName, $RawData.Count)
} -Verbose