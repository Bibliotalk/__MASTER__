export default function register(api: any) {
  // Bibliotalk Acquisition Plugin
  // Intended responsibilities:
  // - Ingest URLs/files
  // - Convert to markdown canon entries
  // - Write `memory/__CANON__/` + `index.json`

  api?.log?.info?.("[bibliotalk-acquisition] loaded");

  // TODO: implement tools (snake_case), e.g. `acquire_canon`.
  // api.registerTool?.({ name: "acquire_canon", ... })
}
