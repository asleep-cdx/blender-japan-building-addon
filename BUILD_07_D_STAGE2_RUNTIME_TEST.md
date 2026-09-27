# Build 07-D Stage 2 — Blender 5.2 LTS Runtime Test

対象は schema 4 の L Stair。Acceptance Record は本テスト完了後に別途更新する。各操作前後は Object Transform が identity、Managed Stair が1個、Mesh datablock が1個であることを確認する。

## Test 0 — Candidate identity / regressions
07-C Straight と Stage-1保存済みLを開き、loadだけではschema、Path、point ID、AUTO snapshot、Material pointer、Meshが変更されないことを Console で記録する。version `(0, 7, 3)` と説明文も確認する。

## Test 1 — rotated creation and guides
30°回転したLを作成する。Shiftなしはraw free candidate、Shiftありは既存15°制約となることを確認する。P1確定後はcursorを90°位置から大きく外してもconfirmed P0-P1とP1から左右へ伸びる2本の90°guideが常時表示されることを確認する。第3点では10 px以内のexact 90°、world X/Y、既存Path点、segment extension/parallel、visible managed Wall endpoint X/Y guideだけがsnapし、90°guideへ近づくとcandidate Pathが表示されることを確認する。threshold外でclickした場合はwarning後もmodalとpersistent guideが継続する。曖昧な等距離candidateもcommitされず、Wallに接続・split・依存は作られない。

## Test 2 — START / TURN / END relocation and Undo
3ボタンを順に操作する。移動中はcurrent Path、candidate Path、moving marker、active guideを確認し、full Meshがmouse moveごとに交換されないことを確認する。START/ENDのShiftは15°とexact 90°が両立するときだけ成立し、TURNはThales circle上、Shift+TURNは15°rayとexact 90°の同時解となることを確認する。各操作ごとに **UI operation → Ctrl+Z → Ctrl+Shift+Z → Console** の順を厳守し、途中でConsoleを開かない。最後にpoint ID、Stair ID、Material、identity Transform、one Managed Meshを確認する。ESC/RMBはdraw handlerを消し、同じsnapshotを保持する。

## Test 3 — numeric Path / AUTO
P0/P1/P2を数値編集し、strict 90°だけが成功すること、AUTOがPath/幅変更で再配分され、上端高さがexactであることを確認する。non-90°、短いFlight、invalid nosing等はPath・Mesh・allocationを一切変えない。

## Test 4 — distribution lifecycle
AUTO allocationを記録してMANUALへ切替え、同じ値が初期値になることを確認する。合計一致かつ各Flight 2以上のmanual edit、Path move後のphysical segment count保持、MANUAL→AUTO再計算を確認する。合計不一致、1以下、geometry不成立はatomic rollbackする。

## Test 5 — Residential L visual review
代表4組（STEPPED_CLOSED/STEPPED/SQUARE、STEPPED_CLOSED/SLOPED/BEVEL、SLOPED_CLOSED/STEPPED/ROUND、SLOPED_CLOSED/SLOPED/SQUARE）をまとめて確認する。LEFT/RIGHT/BOTH/OFFも切替える。lower Flightのfirst tread/riser、nosing、Side Board reveal、SLOPED_CLOSED下面が維持されることを基準に、Landing approach/outgoing board returnとtop-arrival capが垂直であること、Landing approach edgeだけにnosing/SQUARE/BEVEL/ROUNDが反映されること、outer 90° board cornerにgapがないことを確認する。Landing TREADとUNDERBODYは踏板下面で接するだけで体積が重ならず、Landing下面が巨大なstair-width依存boxではなくhorizontal soffitとoutgoing transitionで上Flightへ接続すること、upper FlightのSide Board revealと下面が同一local frameで揃うこと、左右Turnともboardがopeningを横切らないことを目視する。

## Test 6 — Material and lifecycle
Landing=TREAD、body=UNDERSIDE、board=SIDE_BOARDでLANDING roleがないことをConsoleで確認する。Material pointerを設定し、Reverse、Regenerate、Repair、Save、Blender完全終了、再open後もslot/pointer、canonical Path順、physical allocationが保持されることを確認する。

## Test 7 — rollback / isolation / final review
invalid numeric/mouse/MANUAL/Residential候補を試し、old Mesh、Path、IDs、allocation、dimensions、Material、Stair ID、Transformが不変でpartial Meshがないことを記録する。passive Wall endpoint alignment後にWall move/deleteしてもStairが追従しないこと、Finish/Wall topologyが不変なことを確認する。最後にFlight1 body→Landing body→Flight2 bodyおよびSTEPPED/SLOPED Side Boardのlocal LEFT/RIGHT turn continuationにgap、spike、巨大overlap、world-side反転がないことを目視する。
