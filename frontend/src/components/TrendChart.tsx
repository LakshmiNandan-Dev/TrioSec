import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SEVERITIES, SEVERITY_COLORS, type TrendPoint } from "../api/types";

function formatDate(value: string | null): string {
  if (!value) return "";
  const d = new Date(value);
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, "0")}:${String(
    d.getMinutes(),
  ).padStart(2, "0")}`;
}

export default function TrendChart({ points }: { points: TrendPoint[] }) {
  if (points.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-gray-200 bg-white text-sm text-gray-400">
        No completed scans yet — trends appear after the first scan finishes.
      </div>
    );
  }
  const data = points.map((p) => ({ ...p, label: `#${p.scan_id} ${formatDate(p.finished_at)}` }));
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <h3 className="mb-2 text-sm font-semibold text-gray-700">Findings over time</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -18 }}>
          <CartesianGrid stroke="#e1e0d9" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fill: "#898781", fontSize: 11 }}
            axisLine={{ stroke: "#c3c2b7" }}
            tickLine={false}
          />
          <YAxis
            allowDecimals={false}
            tick={{ fill: "#898781", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{ fontSize: 12, borderRadius: 8, borderColor: "#e1e0d9" }}
            cursor={{ stroke: "#c3c2b7", strokeDasharray: "3 3" }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {SEVERITIES.map((sev) => (
            <Line
              key={sev}
              type="monotone"
              dataKey={sev}
              name={sev}
              stroke={SEVERITY_COLORS[sev]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, strokeWidth: 2, stroke: "#fcfcfb" }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
