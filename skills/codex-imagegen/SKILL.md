---
name: codex-imagegen
description: Generate or edit raster images from another agent through an authenticated local Codex CLI that actually exposes image generation. Use for requested imagery and required raster assets; in a Codex session with a native image tool, use that tool directly instead of recursively invoking this bridge.
metadata:
  version: "2.0.0"
---

# Codex image bridge

本项目的回执相对路径与落盘约定见 [PROJECT_COPY.md](PROJECT_COPY.md)。当前 Codex 会话有原生图片工具时直接使用，结果必须复制进本轮工作区。

Call an available Codex CLI from another agent to generate or edit a raster asset. The bridge requires Python 3.10+, a local Codex CLI, ChatGPT authentication and an enabled image-generation capability. Installation of this skill does not grant account access or image tools.

## Capability before execution

If the current Codex session already exposes a native image tool, use it directly and follow its image skill. Do not call this bridge from that image-generation session and create a recursion.

Run the script from its actual installed package path:

```text
python <skill-root>/scripts/gen_image.py --check
```

The read-only probe reports CLI version, ChatGPT login, feature flag and supported exec interface. A passing preflight is a candidate environment, not proof that this account/runtime can generate. A real image result plus visual review supplies that evidence. If the flag/interface is absent, do not invent it, change login/configuration or enable a feature silently.

The Python entrypoint works without Bash, BSD stat, find, file or macOS image utilities. Use the system's actual Python command (python3, python, or py -3 as appropriate). Native Windows/Linux generation still needs validation on those systems; portable source is not runtime proof.

## Generate or edit

Save a UTF-8 prompt file or supply UTF-8 stdin, then run:

```text
python <skill-root>/scripts/gen_image.py --workdir <project> --slug hero --prompt-file <prompt.txt>
python <skill-root>/scripts/gen_image.py --workdir <project> --out outputs/revision.png --ref <reference.png> --prompt-file <prompt.txt>
```

`--ref` is repeatable. The original `scripts/gen-image.sh` entrypoint remains a POSIX compatibility wrapper with the same workdir/out/slug/ref arguments and stdin prompt behavior. Windows should call Python directly rather than requiring Git Bash.

The wrapper keeps `workspace-write` and `--skip-git-repo-check` fixed. It does not accept sandbox overrides, change Codex config/auth, select a different model, or automatically fall back to a paid API. Output must resolve inside the selected workspace.

Only the final absolute PNG path is printed on stdout. Logs and a receipt remain under the project's `.codex-imagegen/<run-id>/` for diagnosis. Do not commit private prompts or account logs. Existing outputs are preserved with a numbered filename; each call uses an isolated staging path. Recovery accepts only the explicit fresh result returned by that invocation, never the newest image in a shared directory.

## Prompt and reference handling

```text
Asset purpose: Product launch hero.
Primary request: The user's actual requested subject/action.
Input images: Image 1 is the approved product; preserve its geometry and labels.
Style and composition: Requested medium, crop, focal subject and usable negative space.
Lighting and color: Relevant direction from the brief.
Text (verbatim): "Exact requested text"
Constraints: Identity and details that must remain unchanged.
Avoid: Unrequested marks, objects or typography.
Output: Requested aspect ratio and transparency.
```

Preserve a detailed user prompt rather than adding unrelated art direction. For an edit, state invariants and the exact change. Request transparent background when required. Use native image-tool parameters where available; do not treat old size claims as a current API contract. A precise output size requires an explicitly chosen crop/fit operation after reviewing the generated composition.

Generate only what the task needs, one image at a time. A task mentioning a website or video does not by itself authorize arbitrary asset batches. Do not substitute synthetic product details when authentic product assets are required.

## Review and failure handling

Inspect every actual image with the available image-view tool. Check subject identity, requested change, composition, text, edges/transparency and unintended elements. PNG signature and dimensions confirm only a file header; they do not prove a valid complete image or a correct creative result.

Iterate on a specific observed defect and preserve versions. On timeout, unavailable tool or uncertain result, inspect this run's log and reconcile before retrying. An already generated image can exist even when copying failed. Report actual limits; do not silently create a placeholder or switch provider/authentication.
