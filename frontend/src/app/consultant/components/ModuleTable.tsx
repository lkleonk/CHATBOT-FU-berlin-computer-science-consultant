import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";

export type PlannedModuleRow = {
  id: string;
  name: string;
  lp: number;
  area: string;
  isWahlbereich: boolean;
  isUngraded: boolean;
  isBachelorModule: boolean;
};

type ModuleTableProps = {
  rows: PlannedModuleRow[];
};

export function ModuleTable({ rows }: ModuleTableProps) {
  if (rows.length === 0) {
    return (
      <Typography variant="body2" sx={{ color: "text.secondary" }}>
        No modules available.
      </Typography>
    );
  }

  return (
    <TableContainer>
      <Table size="small" aria-label="planned modules">
        <TableHead>
          <TableRow>
            <TableCell>Module</TableCell>
            <TableCell align="right">LP</TableCell>
            <TableCell>Area</TableCell>
            <TableCell>Markers</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => {
            const markers = [
              row.isWahlbereich ? "Wahlbereich" : null,
              row.isUngraded ? "Ungraded" : null,
              row.isBachelorModule ? "Bachelor" : null,
            ].filter(Boolean);

            return (
              <TableRow key={row.id}>
                <TableCell>{row.name}</TableCell>
                <TableCell align="right">{row.lp}</TableCell>
                <TableCell>{row.area}</TableCell>
                <TableCell>{markers.join(", ") || "-"}</TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
