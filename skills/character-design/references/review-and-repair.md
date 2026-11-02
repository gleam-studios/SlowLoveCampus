# Garment and Character Asset Review and Repair

Read the rendered image itself. The prompt is not evidence that the requested design appeared.

## Four-view Garment Acceptance Checks

1. **Design fidelity:** every locked garment, shoe, accessory, color, material, closure, and prohibited-substitution rule is respected.
2. **View consistency:** front, back, left, and right depict the same design. Check repeated-element count, side placement, hem length, seams, hardware, shoes, and accessory quantity.
3. **Physical credibility:** projecting parts have supports; transparent parts have thickness and edges; fabric responds to gravity and body volume; shoes contact the floor.
4. **Air mannequin:** no face, skin, hair, neck, hands, legs, feet, or visible mannequin shell appears. Garments retain believable support.
5. **Capture realism:** the neutral background and light match the chosen realistic/CG/AAA treatment; a real white wall is required only for the photographic branch; shadows and reflections are plausible.
6. **Framing:** the four views are complete, similarly scaled, ordered front/back/left/right, and not cropped.

Accept only when there is no major identity, structure, material, or mannequin failure. Minor camera or lighting variation is acceptable when it does not alter the garment.

## Single-variable Repair

Classify the observed defect for diagnosis; classification does not authorize changing the prompt or design:

- `DESIGN_DRIFT`
- `VIEW_INCONSISTENCY`
- `MATERIAL_FAKE`
- `ATTACHMENT_IMPOSSIBLE`
- `VISIBLE_BODY`
- `CAPTURE_OR_LAYOUT`

Preserve the prompt, references, parameters, requested aspect ratio and accepted design. For a generation defect, rerender under the exact same conditions within the task authorization. Do not edit the design, prompt, layout or template as an automatic repair.

For `VIEW_INCONSISTENCY`, rerender without changing the locked counts or structure. Changing counts, attachment landmarks or simplifying a design requires a user-requested revision; do not inflate the universal template.

For `MATERIAL_FAKE`, preserve the established material requirements and rerender. Do not rewrite the selected style or prompt merely because one result failed.

For `VISIBLE_BODY`, rerender with the existing invisible-support prompt; do not add defensive constraints automatically.

Report: status, visible evidence, preserved elements, one repair variable, and new version path.

## Character Styling Asset Acceptance Checks

1. **Identity:** every face remains the same identity as Image 1; bone structure, age, skin tone, body proportions, and selected hair state are unchanged.
2. **Image preservation:** panel count, viewpoint, pose, framing, background, lighting, and overall composition follow Image 1.
3. **Outfit fidelity:** Image 2's complete garments, shoes, accessories, materials, sides, quantities, layers, and wearing relationships appear consistently wherever visible.
4. **Controlled styling:** only the filled keep-list makeup/hair changes appear; every do-not-keep item is absent; the established skin/surface, lip, lash and hair treatment remains consistent.
5. **Physical fit:** neckline, shoulders, chest, waist, hips, sleeves, hosiery, and footwear have credible contact, tension, folds, occlusion, support, and gravity.
6. **Human integrity:** inspect every hand, finger group, foot, arm, leg, ear, and facial feature in every panel. Nothing is missing, duplicated, fused, cropped unexpectedly, or anatomically impossible.
7. **Capture realism:** skin, cloth, leather, metal, transparent materials, shadows and reflections match the established realistic, general CG or AAA style. A deliberately plastic/toy style is valid when specified.

## Rerender Defects Without Changing Inputs

- Generation defects (identity drift, inconsistent garment views, missing hands, fused fingers, edge crops, wrong output proportions) call for a new candidate with the exact same prompt, references and settings. The requested ratio stays fixed; do not repair a 9:16 asset by changing it to landscape.
- Repeated failures do not automatically authorize changing the design, prompt, proportions, crop, template or workflow. At the task's budget/attempt limit, report what failed and retain useful candidates.
- Only change the creative requirements when the user requests a design/styling revision; distinguish that request from a failed sample.
- Save new candidates as versions; select one usable result for the same intended asset rather than creating a second redundant asset stage.

Report actual acceptance status, observed defects, unchanged input conditions, adopted version and known limits.
