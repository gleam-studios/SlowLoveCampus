# Build an Approved Character Styling Picture

Use an already selected outfit directly; for a newly designed outfit/styling, obtain user confirmation before application. Do not repeat existing confirmation.

## Find the Identity Reference

Use the base board supplied or selected by the user as Image 1. A single image may be an intermediate edit target, but is not by itself a complete character reference board. It may depict a real person or a fictional character, in a single photograph or a multi-view identity sheet. Do not assume a particular project, character, filename, hairstyle, or body type. If several base images are available, choose the one matching the user's requested subject and hair state; ask only if the intended identity cannot be determined reliably.

Body-reference sheets may be consulted only when needed to understand proportions or garment contact. They do not change the requested outfit coverage or imply unclothed output.

## Use the Character-styling Template

Use [../assets/character-styling-template.txt](../assets/character-styling-template.txt). Fill its style, explicit-change and keep/remove fields; retain the reference-authority contract. The keep/remove fields mean:

- the first `{{用户输入}}` under “保留的妆造”: styling that must remain or be newly designed and applied;
- the second `{{用户输入}}` under “不保留的妆造”: styling that must not appear.

The reusable body of the prompt is already the reference-authority contract. Do not surround it with a second competing workflow.

## Separate Reference Roles

- **Image 1 — edit target and identity authority:** locks face, hair state, skin, body proportions, recognizable identity, pose, expression, camera, layout, background, lighting, and overall image expression.
- **Image 2 — approved complete outfit:** locks every garment piece, material, color, seam, closure, repeated-element count, footwear, accessory, and wearing relationship. It does not change the person or composition.
- **Images 3–N — named detail references:** clarify only the corresponding clothing, accessory, prop, or makeup detail; they never replace Images 1 or 2.

Label these roles explicitly in the generation prompt. Never blend their authority.

## First Output Is a Character Styling Asset

Preserve Image 1's full structure. If Image 1 is a multi-view identity board, keep its panel arrangement, viewpoints, framing, background, and lighting while replacing the visible base clothing consistently in every relevant panel. If Image 1 is a single photograph, preserve that photograph's pose and composition.

Require:

- the exact identity from Image 1 and selected hair state;
- exact approved outfit without redesign or simplification;
- natural contact at neck, shoulders, chest, waist, hips, limbs, and shoes;
- believable tension, folds, occlusion, support, and gravity;
- complete hands, feet, limbs, and repeated panel views wherever present in Image 1;
- the character’s established style: natural photography for realistic, specified 3D materials for CG, or photorealistic CGI for AAA.

Review the result against every supplied reference. Review identity, garment fidelity, makeup, and anatomy. Deliver the usable asset with its confirmation status; do not add a mandatory post-render approval gate. Shot production is handled elsewhere.

## Transfer Boundaries

- Replace Image 1's original clothing completely, but retain its pose, layout, background, lighting, and overall image effect unless the user explicitly requests a new scene.
- Do not infer new garment details from the subject's body reference.
- Do not change the approved outfit to flatter the model; preserve the design and solve fit through realistic tailoring and fabric behavior.
- Do not change hair state or body proportions merely to suit the garment. Change makeup or hair only through the filled controlled-styling fields.

## Explicit Changes

The user’s named hair, makeup, expression and state changes override corresponding preserved values in Image 1, never the identity. All unnamed fields stay fixed. State-only work uses [variants.md](variants.md) without requiring an outfit image.
