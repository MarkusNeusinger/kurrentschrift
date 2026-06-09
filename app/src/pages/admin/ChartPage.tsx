// Thin route mount for `/admin/chart` — the actual editor lives in
// sections/admin/chart.

import { ChartView } from '@/sections/admin/chart/ChartView';

// Default export for React.lazy route splitting (routes/sections).
export default function ChartPage() {
  return <ChartView />;
}
