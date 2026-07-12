function configuredValue(value: string | undefined, fallback: string) {
  return value?.trim() || fallback;
}

const configuredFields = {
  name: process.env.NEXT_PUBLIC_LEGAL_NAME?.trim(),
  street: process.env.NEXT_PUBLIC_LEGAL_STREET?.trim(),
  cityLine: process.env.NEXT_PUBLIC_LEGAL_CITY?.trim(),
  country: process.env.NEXT_PUBLIC_LEGAL_COUNTRY?.trim(),
  email: process.env.NEXT_PUBLIC_LEGAL_EMAIL?.trim(),
};

/**
 * Public provider details rendered on the Impressum and Datenschutz pages.
 * Real deployment values belong in build-time environment variables, not in
 * the repository. The fallbacks make missing production configuration visible.
 */
export const legalContact = {
  name: configuredValue(configuredFields.name, "Name des Anbieters"),
  street: configuredValue(configuredFields.street, "Straße und Hausnummer"),
  cityLine: configuredValue(configuredFields.cityLine, "PLZ Ort"),
  country: configuredValue(configuredFields.country, "Deutschland"),
  email: configuredValue(configuredFields.email, "E-Mail-Adresse einsetzen"),
};

export const isLegalContactConfigured = Object.values(configuredFields).every(Boolean);
