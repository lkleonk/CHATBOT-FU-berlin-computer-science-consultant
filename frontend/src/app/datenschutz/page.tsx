import type { Metadata } from "next";

import {
  LegalConfigurationNotice,
  LegalPageShell,
  LegalSection,
} from "@/components/LegalPageShell";
import { ObfuscatedEmail } from "@/components/ObfuscatedEmail";
import { isLegalContactConfigured, legalContact } from "@/config/legalContact";

export const metadata: Metadata = {
  title: "Datenschutzerklärung | Modulio",
  description: "Informationen zur Verarbeitung personenbezogener Daten durch Modulio.",
};

export default function DatenschutzPage() {
  return (
    <LegalPageShell
      eyebrow="Datenschutz"
      title="Datenschutzerklärung"
      lead="Diese Datenschutzerklärung erläutert die Verarbeitung personenbezogener Daten bei der Nutzung von Modulio. Stand: 24. Juni 2026."
    >
      {!isLegalContactConfigured && <LegalConfigurationNotice />}

      <LegalSection title="1. Verantwortlicher">
        <address>
          {legalContact.name}
          <br />
          {legalContact.street}
          <br />
          {legalContact.cityLine}
          <br />
          {legalContact.country}
        </address>
        <p>
          E-Mail: <ObfuscatedEmail email={legalContact.email} />
        </p>
      </LegalSection>

      <LegalSection title="2. Hosting und technische Zugriffsdaten">
        <p>
          Beim Aufruf der Website verarbeiten der Webserver und der Hosting-Anbieter technisch
          notwendige Zugriffsdaten. Dazu können insbesondere IP-Adresse, Zeitpunkt des Zugriffs,
          angeforderte Ressource, Referrer, Browser- und Betriebssysteminformationen sowie
          Server-Logdaten gehören.
        </p>
        <p>
          Die Verarbeitung dient der sicheren und stabilen Bereitstellung des Angebots. Sie
          erfolgt auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO. Speicherdauer und konkreter
          Hosting-Anbieter richten sich nach der jeweiligen Bereitstellungskonfiguration und
          müssen vom Betreiber vor der Veröffentlichung ergänzt werden.
        </p>
      </LegalSection>

      <LegalSection title="3. Beratungsanfragen und LLM-Verarbeitung">
        <p>
          Wenn Sie eine Nachricht senden, verarbeitet der Backend-Dienst den Nachrichteninhalt,
          eine zufällig erzeugte Sitzungs-ID und die für die Antwort benötigten bisherigen
          Sitzungsdaten. Eingaben werden an den für diese Bereitstellung konfigurierten
          Sprachmodell-Dienst übermittelt. Eine Anfrage kann mehrere Modellaufrufe auslösen.
        </p>
        <p>
          Die Verarbeitung ist erforderlich, um die ausdrücklich angeforderte Studienberatung
          bereitzustellen. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO. Bitte übermitteln Sie
          keine Daten, die für die Beratung nicht erforderlich sind.
        </p>
      </LegalSection>

      <LegalSection title="4. Upload von Leistungsübersichten">
        <p>
          Der optionale PDF-Upload überträgt die Datei an den Backend-Dienst. Dort wird Text aus
          der PDF extrahiert und ungekürzt an den konfigurierten Sprachmodell-Dienst gesendet,
          um Module und Leistungspunkte zu erkennen. Bildbasierte oder unzureichend lesbare PDFs
          werden abgelehnt. Die maximale Dateigröße beträgt 15 MB.
        </p>
        <p>
          Im regulären Sitzungszustand werden anschließend nur der strukturierte Studienplan und
          das Ergebnis der regelbasierten Prüfung weitergeführt, nicht der rohe extrahierte
          PDF-Text. Ist die diagnostische WizardFlow-Aufzeichnung aktiviert, kann der
          unredigierte extrahierte Text jedoch zusätzlich in einer lokalen Trace-Datei auf dem
          Anwendungsserver gespeichert werden. Der Nutzungsdialog zeigt an, ob diese Aufzeichnung
          aktiviert ist.
        </p>
      </LegalSection>

      <LegalSection title="5. Sitzungs- und Browserdaten">
        <p>
          Der Backend-Dienst hält Sitzungsdaten im Arbeitsspeicher. Standardmäßig werden inaktive
          Sitzungen nach 48 Stunden bei der nächsten Bereinigungsgelegenheit entfernt; ein
          Neustart des Dienstes löscht den Arbeitsspeicher ebenfalls. Über „Reset conversation“
          kann die aktuelle Sitzung vorher gelöscht werden. Eine bereits laufende Anfrage wird
          zunächst abgeschlossen.
        </p>
        <p>
          Der Browser speichert die Sitzungs-ID, angezeigte Chatnachrichten und strukturierte
          Studienplandaten im <code>sessionStorage</code>. Darstellungs- und Dialogeinstellungen
          werden im <code>localStorage</code> gespeichert. Diese Daten verbleiben im verwendeten
          Browser, bis der jeweilige Browserspeicher endet oder zurückgesetzt wird.
        </p>
      </LegalSection>

      <LegalSection title="6. Nutzungslimit und IP-Adresse">
        <p>
          Zur Durchsetzung des täglichen Nutzungslimits führt der Backend-Dienst einen
          prozesslokalen Zähler je Client-IP-Adresse. Der Zähler wird um 00:00 Uhr UTC und bei
          einem Neustart des Backend-Prozesses zurückgesetzt. Die Verarbeitung dient dem Schutz
          des Dienstes vor Überlastung und Missbrauch und erfolgt auf Grundlage von Art. 6 Abs. 1
          lit. f DSGVO.
        </p>
      </LegalSection>

      <LegalSection title="7. Diagnosedaten">
        <p>
          Wenn WizardFlow aktiviert ist, können Eingaben, interne Prompts, Modellausgaben,
          Fehlerdetails und Ergebnisse lokaler Prüfschritte in Trace-Dateien auf dem
          Anwendungsserver gespeichert werden. Diese Dateien können personenbezogene Daten und
          unredigierten Transkripttext enthalten und unterliegen nicht automatisch der
          48-stündigen Sitzungslöschung. Der Betreiber muss für die konkrete Bereitstellung einen
          Zugriffsschutz und eine Löschfrist festlegen.
        </p>
      </LegalSection>

      <LegalSection title="8. Empfänger und Auftragsverarbeiter">
        <p>
          Empfänger können der Hosting-Anbieter und der jeweils konfigurierte LLM-Anbieter sein.
          Je nach Bereitstellung wird das Modell über AcademicCloud, einen FU-internen
          Ollama-Dienst oder einen lokal betriebenen Ollama-Dienst angesprochen. Der Betreiber
          muss vor Veröffentlichung die tatsächlich eingesetzten Empfänger, deren Standorte und
          gegebenenfalls geeignete Garantien für Drittlandübermittlungen konkret benennen.
        </p>
      </LegalSection>

      <LegalSection title="9. Cookies, Analytics und Tracking">
        <p>
          Modulio setzt nach aktuellem Stand keine eigenen Cookies ein und verwendet keine
          Analytics-, Werbe- oder Tracking-Dienste. Die oben beschriebenen Browser-Speicher
          dienen ausschließlich der Funktion und Darstellung des Angebots.
        </p>
      </LegalSection>

      <LegalSection title="10. Rechte betroffener Personen">
        <p>
          Im Rahmen der gesetzlichen Voraussetzungen bestehen insbesondere Rechte auf Auskunft,
          Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und
          Widerspruch. Außerdem besteht ein Beschwerderecht bei einer zuständigen
          Datenschutzaufsichtsbehörde.
        </p>
      </LegalSection>

      <LegalSection title="11. Aktualisierungen">
        <p>
          Diese Datenschutzerklärung ist anzupassen, wenn sich Hosting, LLM-Anbieter,
          Protokollierung, Speicherdauern oder andere Verarbeitungsvorgänge ändern.
        </p>
      </LegalSection>
    </LegalPageShell>
  );
}
