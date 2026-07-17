import { CompareTabs } from '@/sections/admin/compare/CompareTabs';

// Thin route mount — the section component carries the whole comparison view
// (letters tab + the connected-writing specimen tabs).
export default function ComparePage() {
  return <CompareTabs />;
}
