export const DEV_TOOLS_ENABLED =
  (process.env.NEXT_PUBLIC_ENABLE_DEV_TOOLS ?? "true").toLowerCase() === "true";
