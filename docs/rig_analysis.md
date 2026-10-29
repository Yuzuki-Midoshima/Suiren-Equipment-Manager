# ab_rig_B 武器リグ静的解析

対象: [applibot-rig](https://github.com/applibot-inc/applibot-rig)で公開されている
Suirenリグ。解析用リグ本体は本リポジトリに含めない。

## 結論

メッシュ Transform ではなく既存武器リグを制御する。剣メッシュはジョイントで
スキニング済みで、ルートコントローラーから変形されるためである。本ツールは
各ルート直上の既存 `*_parent_target` にのみ専用 parentConstraint を追加する。
スキン、ジョイント、メッシュ階層、既存コンストレイントは変更しない。

| UI武器 | メッシュ | スキン/ジョイント | 操作ルート | 追従対象 |
|---|---|---|---|---|
| Sword 001 | Geo_C_Sword_001 | skinCluster123 / Jnt_C_Sword_01_* | Rig_C_SwordARoot | Rig_C_SwordARoot_parent_target |
| Sword 002 | Geo_C_Sword_002 | skinCluster124 / Jnt_C_Sword_02_* | Rig_C_SwordBRoot_001 | Rig_C_SwordBRoot_001_parent_target |
| Sheath | Geo_C_Sheath | skinCluster139 / Jnt_C_Sword_03 | Rig_C_SwordBSaya_001 | Rig_C_SwordBSaya_001_parent_target |
| Sword 003 | Geo_C_Sword_003 | S_01:skinCluster123 / Jnt_C_Sword_03_* | Rig_C_SwordARoot_02 | Rig_C_SwordARoot_02_parent_target |
| Spear | Geo_C_Spear / Geo_C_Spear_ghost | skinCluster165 / 167 / Jnt_*_Spear_* | Rig_C_Spear_001 | Rig_C_Spear_001_parent_target |
| Stick | Geo_C_Stick | skinCluster168 / Jnt_*_stick_* | Rig_C_Stick_001 | Rig_C_Stick_001_parent_target |

`Geo_C_Sword_002_002` は `Rig_C_SwordB_dummy_001` に既存 parentConstraint され、
`Rig_Other.Sword_B_dummy` で表示制御される Sword B のダミーである。独立武器として
扱わない。`Geo_C_Sheath` も Sword B 表示グループに属する。

## 手と既存接続

- 最終手ジョイント: `Jnt_R_Hand`, `Jnt_L_Hand`
- 実シーンで確認されたキャラクター左右は命名文字と逆のため、UIの右手は
  `Jnt_L_Hand`、UIの左手は`Jnt_R_Hand`へ対応させる。
- アニメーター用 IK: `Rig_R_Hand_IK`, `Rig_L_Hand_IK`
- アニメーター用 FK: `Rig_R_Hand_FK`, `Rig_L_Hand_FK`
- IK/FK の双方が最終手ジョイントへ評価されるため、武器追従先は最終手ジョイントを採用。
- 既存の左武器ノード `Rig_L_Weapon_001_offset` は `Jnt_L_Hand` に拘束済みだが、
  全剣共通の安全な装備切替口とは確認できないため再利用しない。

## 表示

- Sword 001: `Rig_Other.sword_A`
- Sword 002 / 鞘 / Bリグ: `Rig_Other.sword_B`
- Sword 003: `Rig_Other.sword_A_02`
- Spear: `Rig_Other.spear`
- Stick: `Rig_Other.stick`

これらは既存リグがメッシュとリグルートへ接続済み。本ツールは接続を作り替えず、
既存属性の値だけを変更する。

## 初期姿勢とアニメーション上の注意

各既存ルートと parent target に初期 Translate/Rotate が設定されている。専用
constraint は `maintainOffset=True` で追加し、セットアップ時のワールド姿勢を維持する。
切替時は操作ルートのワールド行列を切替前に取得し、space enum の変更後に復元する。
キーフレーム操作では space enum を stepped key、操作ルートの T/R を同フレームに記録する。

## 静的解析では保証できない項目

- Maya 2026 Evaluation Manager 上での全フレーム評価とサイクル有無
- リファレンス化されたリグに属性・ノードを追加できる運用か
- 実際の握り方向と左右手ごとの最終アート調整値
- 既存アニメーションを読み込んだショットでの切替連続性
- Undo、保存、再読み込み後の Maya 実機動作

上記は複製シーンで Maya 2026 の実機テストが必要。

