"use client";

import { useSyncExternalStore } from "react";

type ObfuscatedEmailProps = {
  email: string;
};

function subscribeToHydration() {
  return () => undefined;
}

function getClientSnapshot() {
  return true;
}

function getServerSnapshot() {
  return false;
}

export function ObfuscatedEmail({ email }: ObfuscatedEmailProps) {
  const revealed = useSyncExternalStore(
    subscribeToHydration,
    getClientSnapshot,
    getServerSnapshot,
  );
  const separatorIndex = email.indexOf("@");

  if (separatorIndex < 1 || separatorIndex === email.length - 1) {
    return <span>{email}</span>;
  }

  if (!revealed) {
    const user = email.slice(0, separatorIndex);
    const domain = email.slice(separatorIndex + 1).replaceAll(".", " [dot] ");
    return (
      <span>
        {user} [at] {domain}
      </span>
    );
  }

  return <a href={`mailto:${email}`}>{email}</a>;
}
