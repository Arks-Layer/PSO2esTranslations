#!/usr/bin/env python3
# coding=utf8
import codecs
import json
import os
import shutil
import sys
import getopt

json_loc = os.path.join("..", "json")

# load JSON from file
notes_file_name = "SeraphyRoom_SeraphyNote.txt"
try:
    notes_file = codecs.open(os.path.join(json_loc, notes_file_name),
                             mode = 'r', encoding = 'utf-8')
except FileNotFoundError:
    print("\t{0} not found.".format(notes_file_name))
notes = json.load(notes_file)
print("{0} loaded.".format(notes_file_name))
notes_file.close()

generic_lines = {
    "アビリティは\n「<%abi>」。":
        "Its ability is called\n\"<%abi>\".",
    "アビリティは\n「<%abi>」。\n効果の内容は、チップの詳細情報で\n確認できますよ。":
        "Its ability is called\n\"<%abi>\".\nYou can see what it does by\nchecking the chip's details.",
    "解放には\nこのようなチップが必要です。":
        "To release this chip, you will\nneed these material chips.",
    "素材チップは\n日替わりクエストなどで\n手に入りますよ！\nぜひ解放してみてくださいね！":
        "Material chips can be acquired from\nDaily Quests. Please gather materials\nand release this chip!",
    "ぜひ解放してみてくださいね！":
        "Please release it as\nsoon as you can!",
    "チップが解放され\nアビリティ性能が高まりました！":
        "This chip has been released, and\nits ability has been enhanced!",
    "ますます強力になった効果を\nぜひ試してみてくださいね！":
        "Please, try using it again\nand see for yourself how\nmuch stronger it is!",
    "『ＰＳＯ２』や『ＰＳＯ２ｅｓ』に\n登場する方々の記憶や技術が込められた\nチップのようです。":
        "This seems to be a chip containing the\nmemories and skills of someone who\nappears in PSO2 or PSO2es.",
    "どのような効果なのでしょう……？\n<%CHARANAME>さんの\n入手情報、お待ちしております！":
        "What kind of effect is it...?\n<%CHARANAME>,\nwe need you to get your hands\non one so that we can find out!",
    "チップが解放されアビリティが\n「<%abi>」に\nなりました！\n性能もより強化されていますよ！":
        "This chip has been released,\nand its ability has become\n\"<%abi>\"!\nIts performance can also be\nenhanced even further than before!",
    "『ＰＳＯ２』や『ＰＳＯ２ｅｓ』に\n登場する方々が描かれた\nイラストチップのようです。":
        "This seems to be an illustration\nchip featuring someone who\nappears in PSO2 or PSO2es.",
    "もしかしたら\nいつもと違う一面が見られるかも？\nぜひコレクションに加えてくださいね！":
        "Maybe you'll get to see\nanother side of them?\nPlease do your best to\nadd it to your collection!",
    "「ＰＳＯ２ｅｓ」の垣根を超えた\nスペシャルコラボのチップのようです。":
        "This seems to be a special\ncollaboration chip that links\nPSO2es with something else.",
    "『ＰＳＯ２ｅｓ』の垣根を超えた\nスペシャルコラボのチップのようです。":
        "This seems to be a special\ncollaboration chip that links\nPSO2es with something else.",
    "コラボならではのチップ効果が\nあるかもしれませんね！\n入手しましたら\nぜひ見せに来てください！":
        "Collab chips can have special\nunique effects!\nIf you get one, please come\nback here and show me!",
    "『ＰＳＯ２ ＴＨＥ ＡＮＩＭＡＴＩＯＮ』に\n登場する方々が描かれた\nイラストチップのようです。":
        "This seems to be an illustration\nchip featuring someone who\nappears in PSO2 the Animation.",
    "必殺技を記録した\nチップのようです。": 
        "This seems to be a Photon Art chip.",
    "装備したらどのような\n必殺技を繰り出せるのでしょう……！？\nすごく楽しみですね！":
        "What kind of Photon Art can you\nperform by equipping this...?!\nI look forward to finding out!",
    "装備したらどのような\n必殺技を繰り出せるのでしょう…！？\nすごく楽しみですね！":
        "What kind of Photon Art can you\nperform by equipping this...?!\nI look forward to finding out!",
    "このチップは大剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Sword only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは自在槍専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Wired Lance only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは長槍専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Partizan only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは双小剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Twin Daggers only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは両剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Double Saber only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは鋼拳専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Knuckles only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは銃剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Gunslash only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは長銃専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Assault Rifle only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは大砲専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Launcher only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは双機銃専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Twin Machineguns only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは抜剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Katana only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは強弓専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Bullet Bow only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは魔装脚専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Jet Boots only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは飛翔剣専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for Dual Blades only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "このチップは<%wep>専用となります。\n入手された際は\n武器と合わせて装備してくださいね。":
        "This chip is for <%wep> only.\nBe sure to equip an appropriate\nweapon before you try to use it.",
    "法術を記録した\nチップのようです。":
        "This seems to be\na Technique chip.",
    "装備したらどのような\n法術を繰り出せるのでしょう……！？\nすごく楽しみですね！":
        "What kind of Technique can you\nperform by equipping this...?!\nI look forward to finding out!",
    "アイテムの効用が記録された\nチップのようです。":
        "This seems to be a chip\ncontaining the effect of\nsome kind of utility item.",
    "どんな効果があるのか\nぜひ入手して確かめてみてください！":
        "Please get one so we can see\nwhat kind of effect it has!",
    "主に<%ele>属性のチップの解放に\n必要な素材チップとなります。\nＦＵＮチップスクラッチや\n日替わりのデイリークエストで\n入手可能ですよ。":
        "This is a material chip mostly used\nto release <%ele> chips.\nYou can obtain it from Daily Quests\nand from the FUN Chip Scratch.",
    "主にアークスのチップの解放に\n必要な素材チップとなります。\nＦＵＮチップスクラッチや\n日替わりのデイリークエストで\n入手可能ですよ。":
        "This is a material chip mostly used\nto release ARKS chips.\nYou can obtain it from Daily Quests\nand from the FUN Chip Scratch.",
    "様々なチップ解放に\n必要な素材チップとなります。\nＦＵＮチップスクラッチや\n各曜日の日替わりクエストで\n入手可能ですよ。":
        "This is a material chip used to\nrelease all kinds of chips.\nYou can obtain it from Daily Quests\nand from the FUN Chip Scratch.",
    "様々なチップ解放に\n必要な素材チップとなります。\n各曜日の日替わりクエストで\n入手可能ですよ。":
        "This is a material chip used to\nrelease all kinds of chips.\nYou can obtain it from Daily Quests.",
    "主に<%ele>属性の\n一部の強力なチップの解放に\n必要な素材チップとなります。\n日替わりのデイリークエストで\n入手可能ですよ。":
        "This is a material chip mostly used\nto release powerful <%ele> chips.\nYou can obtain it from Daily Quests.",
    "主に<%ele>属性の\n一部の強力なチップの解放に\n必要な素材チップとなります。\n緊急クエストや交換ショップなどで\n入手可能ですよ。":
        "This is a material chip mostly used\nto release powerful <%ele> chips.\nYou can obtain it from Emergency\nQuests and the Exchange Shop.",
    "チップ特装に必要な素材チップです。\n日替わりのデイリークエストなどで\n入手可能です。":
        "This is a material chip used\nfor Chip Specialization. It can\nbe obtained from Daily Quests.",
    "チップ特装に必要な素材チップです。\nクエストなどで入手可能です。":
        "This is a material chip used\nfor Chip Specialization. It can\nbe obtained from various quests.",
    "特装プラグ強化に必要な\n素材チップです。\n日替わりのデイリークエストなどで\n入手可能です。":
        "This is a material chip used for\nupgrading Specialized Plugs.\nIt can be obtained from Daily Quests.",
    "特装プラグ強化に必要な\n素材チップです。\nクエストなどで入手可能です。":
        "This is a material chip used for\nupgrading Specialized Plugs.\nIt can be obtained from various quests.",
    "エネミーの生体を記録した\nチップのようです。":
        "This chip seems to hold data\nfrom an enemy life form.",
    "いつも戦っているエネミーの能力が\nチップになっています！\nどんな力を持っているのか\n楽しみですね！":
        "One of our enemies, fighting\nfor us in the form of a chip!\nI'm looking forward to seeing\nwhat kind of power it has!",
    "エネミーの力さえも味方にして\n戦闘を有利に進めちゃいましょう！":
        "Even enemies' power can\nhelp you out in battle!",
    "このチップは、まれに発生する\n緊急クエストで入手できるようです。\n発生の際は\nぜひ挑戦してみてくださいね！":
        "This chip seems to be available\nin rarely-occurring Emergency\nQuests. If one comes along,\nplease give it a try!",
    "このチップはどちらかというと\nショップでの交換や\n緊急クエスト時の期間限定効果が\nおもな用途になっています。":
        "This chip is mainly used for\ntrading at the Exchange Shop,\nbut it also has a Limited Effect\nin certain Emergency Quests.",
    "交換する前に、チップを解放して\nこのチップ研究室の発見数を\n増やしておくのもお忘れなく！\n発見数が一定の数になるごとに\n私からお礼をさせていただきますよ！":
        "Don't forget to release it before\nyou trade it in, so you can increase\nthe number of discoveries in the\nChip Lab! Each time your total\ndiscoveries reaches a certain\namount, I'll have a reward for you!",
    "正体不明の謎のチップです。\nもし入手されましたら\nぜひ、見せてくださいね！":
        "This is a highly mysterious\nunidentified chip. If you get\none, please show it to me!",
    "あら……\nなんだか、かわいい鳴き声が\n聞こえてくるような……":
        "Oh my...\nI feel like I can hear a\ncute cry coming from it...",
    "時空を超えて出現する特殊エネミーの\nチップのようです。":
        "This is a chip of a special\nenemy that's travelled\nacross space and time.",
    "このチップは\n強化合成の素材として使用すると\nたくさんの経験値を得ることが\nできるようです。\nぜひ、利用してみてくださいね！":
        "It seems like you'll get a lot of\nGrind EXP if you use this chip\nas material for Chip Grinding.\nGo ahead and use it!",
    "アビリティのレベルをアップさせる\nすごく便利なチップのようです！":
        "This seems to be a very useful\nchip that can raise the ability\nlevels of other chips!",
    "アビリティレベルが上がると\n消費ＣＰが下がったり\nチップ効果の発動率が上がったりと\nいいことがたくさんありますよ！":
        "Raising a chip's ability level\ncan have many positive effects,\nsuch as raising its activation\nrate or lowering its CP cost!",
    "チップのアビリティレベルが\nアップすれば、消費ＣＰが下がったり\nチップ効果の発動率が上がったりと\nいいことがたくさん！\nどんどん強化していきましょう！":
        "If you raise a chip's ability level, its\nCP consumption will decrease or its\nactivation rate will increase.\nAll sorts of good things can happen!\nBe sure to raise chips' ability levels\nwhenever you can!",
    "なんと、<%ele>属性で\n★１２以下のチップの\n強化素材として使用すると\nそのチップのアビリティレベルを\n１つアップさせる効果があるんです。":
        "When used to grind a <%ele>\nelement chip of ★12 rarity or less,\nit raises that chip's ability level by 1.",
    "必殺技を強化する効果を持つ\nチップのようです。":
        "This seems to be a chip whose\nability strengthens Photon Arts.",
    "必殺技をバンバン使われる場合は\nとても有効ですよ！\nぜひ入手してくださいね！":
        "It should be very effective if you use\nit when you're knocking seven bells\nout of an enemy with a Photon Art!\nPlease, you have to get one!",
    "しかも、アビリティレベルを\nなんと２０まで上げることが可能です！\nアビリティレベルを上げるほど\nチップの発動率が向上しますよ。":
        "What's more, you can raise its\nability level all the way to 20!\nRaising a chip's ability level will\nmake it activate more often.",
    "このチップは、アビリティレベルを\n２０まで上げることが可能です！\nアビリティレベルを上げるほど\nチップの発動率が向上しますよ。":
        "This chip's ability level can be raised\nall the way to 20!\nRaising a chip's ability level will\nmake it activate more often.",
    "チップの新技術により生まれた\n「ウェポノイドチップ」の\nひとつのようです。":
        "This seems to be one of the\nnext-generation \"Weaponoid\" chips.",
    "通常のチップよりも\n強力な効果だと聞きますが\n一体どんなチップなんでしょう？":
        "I've heard that they have stronger\neffects than other chips.\nWhat kind of chip could it be?",
    "こちらは\nチップの新技術によって生まれた\n新世代のチップ「ウェポノイドチップ」\nのひとつです。":
        "This is one of the next-generation\n\"Weaponoid\" chips created from the\nlatest advances in chip technology.",
    "特定の武器を強化する効果を持つ\nチップのようです。":
        "This seems to be a chip that boosts\ncertain kinds of weapons.",
    "特定の武器を強化する\n効果を持つチップのようです。":
        "This seems to be a chip that boosts\ncertain kinds of weapons.",
    "武器と合わせて装備すると\nとても有効ですよ！\nぜひ入手してくださいね！":
        "It should be very effective\nif you can equip it with an\nappropriate weapon!\nPlease, you have to get one!",
    "よく使う武器と\n組み合わせることができれば\nとても有効ですよ！\nぜひ入手してくださいね！":
        "It should be very effective if\nyou pair it with a weapon\ntype that you use often!\nPlease, you have to get one!",
    "アビリティは\n「<%abi>」。\nエネミーに攻撃をヒットさせると\n<%wep>の必殺技チップの威力がアップ\n＆ＨＰが徐々に回復します！":
        "This chip's ability is called\n<%abi>.\nIt boosts <%wep> PAs and\nrecovers HP when you hit an enemy\nwith an attack!",
    "<%wep>を使うかたならば\nぜひ入手したいチップですね！":
        "You'll definitely want to get this\nchip if you like <%wep> PAs!",
    "アビリティは\n「<%abi>」。\n攻撃ヒット時、装備中の武器が\n<%ele>属性の場合に\n攻撃の威力が増加されます。":
        "Its ability is called\n\"<%abi>\".It increases your ATK if your\nweapon's element is <%ele>\nand you hit with an attack.",
    "★１３チップの特徴として\nこのチップを装備した時に\n<%ele>属性の必殺技・法術の\nチップコストが減少します！":
        "As a ★13 chip, equipping it will\nreduce the equip cost of <%ele>\nelement PAs and Techniques!",
    "ですが、このチップは\nまだ力を秘めているようです。\nさらなる解放が可能と思われます！":
        "However, this chip still seems\nto have some power locked\naway inside. It may be\npossible to release it again!",
    "さらなる解放には\nこのようなチップが必要です。":
        "To release this chip further, you\nwill need these material chips.",
    "素材チップは\n緊急クエストなどで\n手に入りますよ！\nぜひ解放してみてくださいね！":
        "You can obtain these chips from\nEmergency Quests. Please gather\nmaterials and fully release this chip!",
    "チップが真・解放されアビリティが\n「<%abi>」に\nなりました！\n性能もさらに強化されていますよ！":
        "This chip has been fully\nreleased, and its ability is now\n\"<%abi>\"!\nYou can also enhance its\nperformance even further!",
    "真・解放した★１３チップは\n全属性の必殺技・法術の\nチップコストが減少します！":
        "As a fully released ★13 chip,\nequipping it reduces the equip\ncosts of all PAs and Techniques!",
    "マグの性能や技術を記録した\nチップのようです。":
        "This chip seems to be recording\nthe technology and uses of a Mag.",
    "このチップはリンクスロット限定で\nチップパレットには装備できません。\n他のチップと組み合わせることで\n効果を発揮します！":
        "It's limited to Link Slots, so you can't\nequip it on your main Chip Palette.\nYou should get good results from\ncombining it with another chip!",
    "このチップは、★９以上のチップの\nリンクスロットに装備できます。\n<%ele>属性のチップに装備すると\nリンクスキルが発生します。":
        "This chip can be equipped in the\nLink Slot of a ★9 or higher chip.\nIf equipped to a <%ele> element\nchip, its Link Skill will activate.",
    "チップの解放（属性変換）は\n何度でも可能です。":
        "You can release this chip to\nconvert its element to a different\none as many times as you like.",
    "解放（属性変換）には\nこのようなチップが必要です。":
        "To release this chip and convert\nits Element, you will need these\nmaterial chips.",
    "属性は、<%ele>属性に特化したものに\nなっています。\nエネミーによって\n使い分けてみてくださいね。":
        "This chip is intended for use\nwith the <%ele> element.\nTry to choose chips whose\nelements are appropriate for\nthe enemies you'll face.",
    "属性は、炎属性に特化したものに\nなっています。\nエネミーによって\n使い分けてみてくださいね。":
        "This chip is intended for use\nwith the Fire element.\nTry to choose chips whose\nelements are appropriate for\nthe enemies you'll face.",
    "属性は、闇属性に特化したものに\nなっています。\nエネミーによって\n使い分けてみてくださいね。":
        "This chip is intended for use\nwith the Dark element.\nTry to choose chips whose\nelements are appropriate for\nthe enemies you'll face.",
    "属性は、風属性に特化したものに\nなっています。\nエネミーによって\n使い分けてみてくださいね。":
        "This chip is intended for use\nwith the Wind element.\nTry to choose chips whose\nelements are appropriate for\nthe enemies you'll face.",
    "": ""
    }
# Are we printing list of unknown lines to console? Default to no.
reporting = False

try: 
    opts, args = getopt.getopt(sys.argv, "r", ["report"])
except getopt.GetoptError:
    print("Unrecognised option.")

for opt, arg in opts:
    if opt in ("-r", "--report"):
        reporting = True


unknowns = {}

for note in notes:
    # translate generic lines
    if note["jp_text"] != "":# and note["tr_text"] == "":
        if note["jp_text"] in generic_lines:
            note["tr_text"] = generic_lines[note["jp_text"]]
        else:
            if note["jp_text"] in unknowns:
                count = unknowns[note["jp_text"]]
                unknowns.update({note["jp_text"]: count + 1})
            else:
                unknowns.update({note["jp_text"]: 1})

# write JSON back to file
notes_file = codecs.open(os.path.join(json_loc, notes_file_name),
                          mode = 'w', encoding = 'utf-8')
json.dump(notes, notes_file, ensure_ascii=False, indent="\t", sort_keys=False)
notes_file.write("\n")
notes_file.close()

sorted_unknowns = {}

sorted_keys = sorted(unknowns, key=unknowns.get, reverse=True)
for key in sorted_keys:
    sorted_unknowns[key] = unknowns[key]

lines = sorted_unknowns.keys()
for line in lines:
    if sorted_unknowns[line] >= 2:
        if reporting:
            print("{0} counts of unknown line: {1}".format(sorted_unknowns[line], line.replace("\n", "\\n")))
