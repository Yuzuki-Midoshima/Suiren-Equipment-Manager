# Suiren Equipment Manager

[![CI](https://github.com/Yuzuki-Midoshima/Suiren-Equipment-Manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Yuzuki-Midoshima/Suiren-Equipment-Manager/actions/workflows/ci.yml)

Autodesk Maya 2026で、アプリボット公開のフリーリグ「スイレン」の装備を管理する
個人制作の非公式拡張ツールです。コンストレイントや階層を直接操作せず、複数の武器を
右手・左手・Worldへ切り替えられます。

本プロジェクトは株式会社アプリボットによる公式ツールではなく、同社との提携・承認を
示すものでもありません。元リグ、モデル、テクスチャ等のアセットは同梱していません。

## 主な機能

- 3系統の剣を個別管理
- 鞘、槍、棒の管理
- Right Hand / Left Hand / Worldの装備先切替
- 切替フレームでのワールド位置維持
- 装備先をstepped keyで記録するアニメーション対応
- 装備先別のTranslate / Rotateオフセット保存
- 保存済みオフセットの自動適用
- 装備ごとの表示・非表示切替
- 追従ON/OFFと状態のキーフレーム登録
- 通常表示／コンパクト表示を切り替えられるPySide6日本語UI
- Undo、再実行、シーン保存・再読み込みに配慮した非破壊設計

## 動作環境

- Autodesk Maya 2026
- Python 3（Maya同梱版）
- PySide6 / shiboken6（Maya同梱版）
- 対象: applibot-rigで公開されているSuirenリグ

外部Pythonパッケージの追加インストールは不要です。リグの更新によってノード構成が
変わった場合は、`suiren_equipment_manager/rig_adapter.py`の更新が必要になることが
あります。

## インストール方法

1. このリポジトリをZIPでダウンロードするか、任意の場所へcloneします。
2. ZIPの場合は必ず展開します。
3. Maya 2026を起動し、登録先にしたいシェルフを選択します。
4. `drag_and_drop_install.py`をMayaのビューポートへドラッグ＆ドロップします。
5. シェルフに追加された`Suiren Equip`ボタンを使用します。

インストール先は任意です。登録後にフォルダーを移動または改名した場合は、移動先の
`drag_and_drop_install.py`をもう一度ドロップしてください。

### 手動登録

MayaのPython Script Editorで次を実行します。

```python
import importlib.util

installer_path = r"展開したフォルダー\register_shelf.py"
spec = importlib.util.spec_from_file_location(
    "suiren_equipment_manager_shelf", installer_path)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)
installer.register()
```

## 起動方法

登録された`Suiren Equip`シェルフボタンを押します。同じシェルフへ再登録すると既存の
ボタンを更新し、重複した旧ボタンを整理します。

## 操作方法

1. 「操作する武器」から対象を選択します。
2. `右手へ / 左手へ / Worldへ`を押すと、その場で装備先が切り替わります。
3. 必要に応じて位置・回転を調整します。
4. 「この握り位置を保存」で、現在の装備先専用のオフセットを保存します。
5. 「キー登録」で装備先、追従状態、位置、回転を現在フレームへ記録します。

保存済みの握り位置がある装備先へ切り替えると、その値を自動適用します。未保存の場合は
切替前のワールド位置を維持します。初回操作時のセットアップは自動です。

コンパクト表示では数値編集と説明を畳み、装備先、追従、表示、握り保存、キー登録へ
すばやくアクセスできます。右手・左手・Worldそれぞれの握り位置保存状態も表示します。

## 対応武器

| UI表示 | 種別 |
|---|---|
| 剣 01 | Sword A系統 |
| 剣 02 | Sword B系統 |
| 剣 03 | Sword A 02系統 |
| 鞘 | Sword Bの鞘 |
| 槍 | Spear |
| 棒 | Stick |

## 技術的な工夫

- メッシュTransformではなく、既存の武器リグ制御ノードを利用
- ツール専用の`SEM_*`ノードを追加し、既存ジョイントやスキンを変更しない
- 既存Transform接続との競合を検出した場合は上書きせず中断
- `maintainOffset`とワールド行列の復元による切替時の位置維持
- Maya標準ノードによる評価で、アニメーション評価をscriptJobへ依存させない
- セットアップ済みノードを再利用し、重複生成を防止
- 名前空間および読み込み時の接頭辞を考慮したノード解決
- 手IKのParent Switchが`root / waist / spine_003`の場合も評価後に位置合わせ
- スイレン固有の接続情報を`rig_adapter.py`へ集約

詳細は[リグ解析メモ](docs/rig_analysis.md)を参照してください。

## 注意事項

- 必ず複製シーンで動作確認してから制作データへ導入してください。
- リファレンス設定や既存接続との競合により、セットアップできない場合があります。
- 複数の同一リグがあるシーンではノード名が曖昧になり、処理を中断する場合があります。
- 既存のアニメーションキーはリセット操作でも削除しません。
- 本ツールは無保証です。使用によって生じた損害について作者および元リグ提供者は責任を
  負いません。
- 元リグの利用は、アプリボットの利用規約に従ってください。規約では非営利目的に限定され、
  リグの二次配布は禁止されています。

## クレジット

- 元リグ: [applibot-inc/applibot-rig](https://github.com/applibot-inc/applibot-rig)
- 元リグ提供: 株式会社アプリボット
- ツール制作: [Yuzuki-Midoshima](https://github.com/Yuzuki-Midoshima)

「Suiren」「スイレン」および元リグに関する権利は、それぞれの権利者に帰属します。
本リポジトリは元リグのコードやアセットを再配布しません。

## ライセンス

本リポジトリの自作ツールコードは[MIT License](LICENSE)で公開します。

MIT Licenseは、元のApplibot Rig、Suirenのモデル、リグ、テクスチャ、画像、名称その他の
第三者コンテンツには適用されません。元リグにはアプリボットの独自利用規約が適用されます。
元リグの利用条件は必ず公式配布元で確認してください。

