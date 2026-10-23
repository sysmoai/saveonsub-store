// Node's built-in TypeScript support strips types but does not resolve the
// extensionless relative imports used by the Pages Functions source. This hook
// retries those specifiers with ".ts" so the real, unmodified source runs.
export async function resolve(specifier, context, nextResolve) {
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
