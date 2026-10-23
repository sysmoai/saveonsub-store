// Node's built-in TypeScript support strips types but does not resolve the
// extensionless relative imports used by the Pages Functions source. This hook
// retries those specifiers with ".ts" so the real, unmodified source runs.
export async function resolve(specifier, context, nextResolve) {
  // Pages Functions import JSON the bundler way (no import attribute); Node
  // needs `type: "json"`, so add it for .json specifiers.
  if (specifier.endsWith(".json")) {
    const resolved = await nextResolve(specifier, { ...context, importAttributes: { ...context.importAttributes, type: "json" } });
    return { ...resolved, importAttributes: { type: "json" } };
  }
  const relative = specifier.startsWith("./") || specifier.startsWith("../");
  if (relative && !/\.[cm]?[jt]s$/.test(specifier)) {
    try {
      return await nextResolve(`${specifier}.ts`, context);
    } catch {
      // fall through to default resolution
    }
  }
  return nextResolve(specifier, context);
}
