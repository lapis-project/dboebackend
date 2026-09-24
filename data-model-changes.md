# Data model changes

## class Beleg

### [adds field Beleg.note](https://github.com/lapis-project/dboebackend/commit/7d733bc952c9f833a8ca16b15c273bf817784dcd)

* JSON field, NOTES_SCHEMA, `./tei:note`

#### [remvoes fields: `Beleg.note_diverse`, `Beleg.note_notabene`](https://github.com/lapis-project/dboebackend/commit/89c2c5d9d077b337f6148b9c55a642942ad54ec5)

* `Beleg.note` with NOTES_SCHEMA captures `./tei:note` and replaces `Beleg.note_anmerkung_b`, `Beleg.note_diverse`, `Beleg.note_notabene`

### [adds field Beleg.xr](https://github.com/lapis-project/dboebackend/commit/460d62440e360a28c26d207188c26abb51370328)

* JSON field, XR_SCHEMA, `./tei:xr`

#### [replaces fields: `Beleg.xr_type_verweise_b`, `xr_type_verweise_o`](https://github.com/lapis-project/dboebackend/commit/89c2c5d9d077b337f6148b9c55a642942ad54ec5)

* `Beleg.xr_node` with XR_SCHEMA captures `./tei:xr` and replaces `Beleg.xr_type_verweise_b`, `xr_type_verweise_o`

### [adds field `Beleg.etymology`](https://github.com/lapis-project/dboebackend/commit/89c2c5d9d077b337f6148b9c55a642942ad54ec5)

* JSON field, ETYMOLOGY_SCHEMA, `./tei:etym`
* `Beleg.etymology` used for serialising `"etym"` -> `Beleg.etymology` needs to be changed/updated to modify `"etym"`

### [adds fields `Beleg.place_qdb` and `Beleg.place_qu`](https://github.com/lapis-project/dboebackend/commit/0b30d3face35f667bd8e969a1a89ba11183e59e5)

* both fields of type ArrayField
* `Beleg.place_qd` captures `./tei:usg[@corresp='this:QDB']/tei:placeName"`
* `Beleg.place_qu` captures `./tei:usg[@corresp='this:QU']/tei:placeName"`
* values of both places serialized into `"ort`

### [adds field `Beleg.ref`](https://github.com/lapis-project/dboebackend/commit/d8f6eedbc3276914a388dd4df5e509fbca68bdd5)

* `Beleg.ref` with REFS_SCHEMA to capture `./tei.ref[@type="seite"|"paragraph"|"karte"|"dbo"|"sni"|"sna"|"quelleDetaillierte"|"quelleNeu"|"quelleZitierte"]`
* replaces fields `Beleg.ref_type_dbo`, `Beleg.ref_type_sni` [see commit](https://github.com/lapis-project/dboebackend/commit/6bd92cac2372cf71587ebd5f257f248f44b26825)
* used to serialize data for fields `"quelle_detaillierte"`, `"quelle_neu"`, `"quelle_zitiert"`, `"verweis"`, `"paragraph"`

### [adds field Beleg.figure](https://github.com/lapis-project/dboebackend/commit/69add8111e6c220e2703e36ee6ae0c0dd460437d)

* `Beleg.figure` of type ArrayField used to capture `./tei:figure/tei:note`, serialized into `"figure"

### [adds field Beleg.quelle_number](https://github.com/lapis-project/dboebackend/commit/9851a5dabaa3ce1e8f4ba298c30e270f361a4331)

* `Beleg.quelle_number`, CharField used to capture `./tei:ref[@type='quelle']/tei:num` and serialized into `"quelle_number"`

## class AnmerkungLautung

### [removes class AnmerkungLautung](https://github.com/lapis-project/dboebackend/commit/51a17e6a315e3a905ca5e584ba5e64908a1fdd19)

* used to store `tei:note` related to a Lautung object
* changes logic of `"anm_lw_star"`

## class Citation (Kontext)

### [removes `Citation.definition`, `Citation.definition_lang`, `Citation.note_anmerkung_b`, `Citation.note_anmerkung_o`, `Citation.note_diverse`, `Citation.xr`](https://github.com/lapis-project/dboebackend/commit/2115753351076a3e5381af4fa1d3e96caba983ef)

### [adds field `Citation.definition_node`, `Citation.note`, `Citation.xr_node`](https://github.com/lapis-project/dboebackend/commit/2115753351076a3e5381af4fa1d3e96caba983ef)

* `Citatin.definition_node` with DEF_SCHEMA captures `./tei:cit/tei:def` and replaces `Citation.definition`, `Citation.definition_lang` and `Citation.definition_corresp`
* `Citation.note` with NOTES_SCHEMA captures `./tei:cit/tei:note` and replaces `Citation.note_anmerkung_b`, `Citation.note_anmerkung_o`, `Citation.note_diverse`
* `Citation.xr_node` with XR_SCHEMA captures `./tei:cit/tei:xr` and replaces `Citation.xr`

### [adds field Citation.re_node](https://github.com/lapis-project/dboebackend/commit/e9c000bdb2aedec3d4f3fdd85e5202fb80a39c06)

* `Citation.re_node` with RE_SCHEMA captures `./tei:cit/tei:re` and replaces `class ZusatzLemma`

### [adds field `Citation.ref`](https://github.com/lapis-project/dboebackend/commit/6bd92cac2372cf71587ebd5f257f248f44b26825)

* `Citation.ref` with REFS_SCHEMA captures `./tei:cit/tei:ref[not(@type='fragebogenNummer')]`
* Data serialized into fields `"pages"` and `"paragraphs"`

## class ZusatzLemma

### [removes class ZusatzLemma](https://github.com/lapis-project/dboebackend/commit/6d3fbac1c88f67e3413f2266122cc791539b1505)

* `class ZusatzLemma` was replaced by `Citation.re_node`

## class Sense (Bedeutung)

### [adds field `Sense.note` replacing `Sense.note_anmerkung_b` and `Sense.note_anmerkung_o`](https://github.com/lapis-project/dboebackend/commit/4acb4280067e8390ede9822c45315ddfaaef1d57)

* `Sense.note.note` with NOTES_SCHEMA captures `./tei:note` and replaces `Sense.note.note_anmerkung_b`, `Sense.note.note_anmerkung_o`
