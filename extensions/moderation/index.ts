export default function register(api: any) {
  // Bibliotalk Moderation Plugin
  // Intended responsibilities:
  // - Enforce AGENTS.md boundary rules
  // - Apply tool gating / allow-deny policies
  // - Run structured checks (classify/flag/escalate)

  api?.log?.info?.("[bibliotalk-moderation] loaded");

  // TODO: implement tools, e.g. `moderate_thread`.
}
