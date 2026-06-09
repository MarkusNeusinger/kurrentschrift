// Thin route mount for `/admin/chart` — the actual editor lives in
// sections/admin/chart. The source guard lives here so ChartView can take
// `source` as a required prop and run all its hooks unconditionally.

import { useAdmin } from '@/context/AdminContext';
import { ChartView } from '@/sections/admin/chart/ChartView';

// Default export for React.lazy route splitting (routes/sections).
export default function ChartPage() {
  const { source } = useAdmin();
  if (!source) return null;
  return <ChartView source={source} />;
}
