# Product-film practice: verified production lessons, 2026-10-06

USER REJECTION: The user explicitly rejected ORBIT as poor-quality imagery/materials. This is a failed visual result. Technical execution observations below remain narrowly useful, but are not evidence of improved aesthetics. Use the mechanisms when relevant, never the lamp design or dark/gold palette as a universal template.

## Decisions tested
- Use one editable 3D asset for multiple shots when geometry, materials and lighting must remain consistent. Camera changes then preserve object identity without separate image-generation guesses.
- Assign different information to each shot: surface/light detail, physical construction, whole-object reveal, final composition. Changing only zoom on one poster is not the same exercise.
- Check full-object framing at the intended aspect ratio and every path endpoint before sequence rendering. The first wide preview clipped the lamp; backing off the camera and changing focal length fixed it.
- Use a cyclorama for a seamless studio when the floor/world boundary becomes a visible line. A plane plus environment can leave a horizon through the image. Correct mesh normals and inspect the actual lighting afterwards.
- Arrange negative space for the final typography in the camera composition. Type cannot rescue an arbitrary product placement after the render.
- Material microvariation must be restrained and evaluated at final scale; arbitrary high-frequency texture can look like render noise.
- Compare representative final-resolution frames before choosing sample budgets. Cold GPU shader compilation distorted the first timing measurement (about 99 seconds versus subsequent previews around 2 seconds). Do not extrapolate from the cold frame or a smaller preview.
- Avoid concurrent GPU renderer processes on the same device unless benchmarked. They contended in this run. Keep one writer per frame directory.
- In this Blender CLI run, SIGINT canceled a current render without reliably ending the surrounding Python loop. To stop a launched batch, verify the owned process exits before resuming. Validate checkpoint PNGs and never let two processes write the same frame.

## Blender 5.1.2 observations
- Apple Silicon Metal device was discovered and used through Cycles preferences in the temporary background process; no user preference file was saved.
- `scene.compositing_node_group` exists and `scene.node_tree` does not in this runtime. Existing recipes referring to older compositor/EEVEE fields must be checked rather than copied blindly.
- `World.use_nodes` and `Material.use_nodes` worked with deprecation warnings. Recheck the API on version changes.
- The animation uses an editable camera/light timeline and a saved .blend. Package source and preserve original asset identity.

## Type and audio
- Bundle suitable licensed fonts when reproducibility matters. Manrope and Noto Sans SC were fetched from Google Fonts with their OFL texts; system PingFang paths were not portable.
- Make the primary message readable at the delivery viewing size. A large render resolution does not make a tiny subtitle readable on a phone.
- The 12-second sound bed and metal resonances were synthesized locally with events at shot transitions. Metering reached about -18 LUFS without clipping. This verifies a technical level target, not perceived mix quality; listening must be separately recorded.

## References and evidence boundaries
- https://mvsm.com/project/paper-pro : project explanation, one product still, and sampled 0.92-second GIF. The full film was not watched.
- https://mvsm.com/project/speaker-bag : project explanation, material/environment still and sampled 0.96-second GIF. Public embed config was unavailable; no bypass attempted.
- https://schoolofmotion.com/blog/how-to-design-for-animation-with-ordinary-folk : introduction read; interview/course not completed.
- https://practicaltypography.com/summary-of-key-rules.html : reviewed hierarchy/spacing considerations; print/body-text sizes are not video title specifications.
- https://docs.blender.org/manual/en/latest/render/cycles/gpu_rendering.html : verified Metal support against official documentation and local execution.

Transfer the discipline of material-specific image-making, distinct shot purposes, real perspective and measured review. Do not equate adding 3D, expensive rendering, gold surfaces or a branded title with good taste.

## Failure analysis after user rejection

The imagery did not establish convincing material or premium product photography. The brass looked like a gold-colored plastic surface; the emitter read as a white strip; the primitive ring/base construction lacked designed manufacturing detail; broad illumination and a generic gradient background did not establish a distinctive visual world. These are the assistant's diagnosis of the rendered frames, not claims that the user named each cause.

The process failure was accepting weak look-development frames and committing to a long sequence render. More samples, resolution, animation and audio could not correct that decision. Future product work must compare close-up and hero frames to a relevant professional benchmark before rendering the sequence. The prior camera/cyclorama fixes repaired technical/compositional defects only; they did not establish good image quality.

Do not reuse ORBIT's model, palette or studio setup as a quality template. Do not create another arbitrary product exercise merely to demonstrate tool usage. Choose a specific visual skill gap and require evidence that the image-making improved before expanding the work.
