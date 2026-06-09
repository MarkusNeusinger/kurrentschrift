import { DiagnosticDialog } from '@/sections/admin/diagnostics/DiagnosticDialog';
import { SetupWizard } from '@/sections/admin/setup-wizard';
import { useAdmin } from '@/context/AdminContext';

// The Einrichtungs-Wizard and the Diagnose modal are mounted once here — driven
// by `wizardGlyph` / `diagnoseGlyph` in the admin context — so the chart
// toolbar AND the sidebar can open them for any glyph from a single instance.
export function AdminModals() {
  const { wizardGlyph, closeWizard, diagnoseGlyph } = useAdmin();
  return (
    <>
      <SetupWizard glyphKey={wizardGlyph ?? ''} open={wizardGlyph != null} onClose={closeWizard} />
      <DiagnosticDialog key={diagnoseGlyph ?? 'none'} />
    </>
  );
}
