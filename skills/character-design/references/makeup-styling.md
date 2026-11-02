# Controlled Makeup and Hair Styling

Use this reference only when building the character styling asset after new outfit/styling design is confirmed; state-only work does not require an outfit.

## Design One Cohesive Styling Direction

When the user asks to design facial styling rather than copy it from a reference, derive one restrained, physically wearable direction from the approved outfit. Specify only the categories that materially define it:

- skin finish and the amount of visible real texture;
- brow handling without identity-changing reshaping;
- eye palette, placement, edge softness, liner, lashes, and restrained highlight;
- blush or contour only if needed, without changing bone structure;
- lip color, finish, edge, and preserved lip texture;
- hairstyle or hair accessories only when the user explicitly authorizes a change;
- facial jewelry or ear accessories with exact side and quantity.

Convert mood words into visible cosmetic decisions. “Cold” might mean low-saturation graphite and taupe placement; “fantasy” must become a named, user-approved cosmetic or wearable object rather than a changed face or non-human skin.

## Fill the Two Control Fields

In the first `{{用户输入}}` under “保留的妆造”, state both identity invariants and the exact styling to apply. In the second `{{用户输入}}` under “不保留的妆造”, name plausible but unwanted drift such as colored contacts, bleached brows, fantasy face markings, black lipstick, heavy false lashes, headpieces, changed hair color, skin smoothing, or face reshaping.

Do not treat the do-not-keep field as a generic negative-prompt dump. Include only exclusions that protect the current design and identity.

## Identity and Realism Boundaries

- Preserve facial proportions, bone structure, age, skin tone, recognizable asymmetry, hairline, and the identity of the user-selected person or character.
- For realistic/AAA preserve pores, fine facial hair, natural lip lines and believable layering; for general CG preserve the established stylized surface and model language instead of forcing photographic detail.
- Do not import the face, body, aura, or character traits of the garment reference.
- Do not let makeup compensate for garment problems. Outfit fidelity and facial styling are separate controls.
