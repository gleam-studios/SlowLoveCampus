# Craft decisions

Judgment aids, not a mandatory style. Numerical starting points are local heuristics, not platform rules.

## Story and attention
- Define the viewer's change: uncertainty to understanding, problem to proof, tension to release. Make it visible.
- Know the focal point and eye path at important moments. Coordinate scale, value, focus, movement and sound around it.
- An opening must establish relevance or curiosity; a quiet image can do this. Avoid generic promises unrelated to the subject.
- Demonstrate real product functions and outcomes. Preserve actual geometry/material/brand. Use accurate visual models in explainers.
- Design the ending's meaning and reading hold; a CTA is not the correct ending for every film.

## Composition and type
- Establish a grid, margins, hierarchy and purposeful empty space. Test at expected viewing size. Contextual wide shots and small subjects can be intentional.
- Contrast scale and value; check silhouette/figure-ground separation. Avoid multiple competing heroes.
- Start with one font family or a complementary pair. Check Chinese glyph coverage and semantic line breaks independently from Latin typography.
- Keep important text within the current platform UI-safe area; do not assume one universal margin. Remove accidental widows, clipped marks and tiny explanatory paragraphs.
- Allocate reading time to actual copy and language at mobile size, not a universal 2.5-second rule.
- Expressive oversized/occluded type still needs a clear reading order. Presenter mattes must share framing and time with the base.

## Motion and editing
- Choose anticipation, action, follow-through, settle and hold as the shot needs. Spacing conveys weight and intention.
- Use a coherent motion family, not arbitrary easing variety. Linear motion fits constant-speed mechanisms; springs fit elastic response.
- Use purposeful lead/lag for related elements; reduce unrelated simultaneous activity.
- Across cuts track position, direction, shape, scale, value/color and meaning. Match some for continuity; break them deliberately for impact.
- Camera movement should reveal, follow, reframe or express viewpoint. Avoid perpetual zoom/orbit/shake without purpose.
- Speed ramps need adequate source frames and legible action; they cannot repair missing action. Inspect interpolation artifacts.
- Blur supports motion; it cannot repair poor spacing or hide illegible typography. Inspect sharp frames too.
- Use graphic matches, motivated occlusion, hard cuts and J/L cuts according to the relationship between shots.
- Vary rhythm through dense/sparse, moving/held, close/wide, sound/silence. There is no universal cut-every-2-seconds rule.

## Photography, color and AI footage
- Decide lens impression, camera height/angle, depth, perspective and focus. Preserve geography, screen direction and eyelines.
- Establish motivated key/fill/separation and material response. A global grade cannot replace lighting.
- Normalize exposure and white balance, then match neighboring shots before adding a look. Protect skin/product identity. Use scopes and viewed images together.
- Assign every reference a job: identity, pose, world, camera, motion or palette. Use the current provider's prompting rules; no universal negative-prompt list.
- Check temporal identity, anatomy, contact, occlusion, shadows/reflections, fabric and object permanence. A first frame cannot prove a whole shot.
- In live-action fusion preserve approved performance and photography. Load the existing fusion skill and project contracts.

## Sound
- Give dialogue, music, atmosphere and effects distinct roles. Not every motion needs a whoosh.
- Align perceived impact, not file start, to visual events. Respect phrases and dialogue cadence; on-beat editing is optional.
- J-cuts can anticipate a speaker/place; L-cuts can carry continuity. Preserve room tone where needed.
- Check intelligibility, masking, harshness, clicks, seams and stereo/mono behavior. Use ducking for clarity.
- Set loudness/true-peak targets for the actual delivery context; do not force -14 LUFS everywhere. Verify after encoding.
- Choose licensed/authorized audio appropriate to the film. Simple synthesized tones are not automatically a professional score.

## Deterministic implementation
- Arbitrary frame order must yield the same image. Asset readiness and video frame seeking are part of that contract.
- Key randomness by element identity and intentional time buckets, not a mutable global sequence.
- Use each framework's supported time/render contract; do not impose a custom render(t) everywhere.
- For manual render(t), compare fresh A with A → B → A and paused frames. Include fonts and asset loading in the test.
- For periodic work require state(T)=state(0), and matching velocity where needed; export [0,T) without an extra endpoint frame.
- Spring formulas need separate critical/over-damped handling when accepting those regimes. A formula dividing by sqrt(1-z*z) cannot accept z=1 unchanged.
