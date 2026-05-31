import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutlined";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { RuleCheckResult, RuleIssue } from "@/types/api";

type RuleCheckPanelProps = {
  result: RuleCheckResult;
  compact?: boolean;
};

function formatKey(key: string) {
  return key.replace(/_/g, " ");
}

function issueIcon(issue: RuleIssue) {
  return issue.severity === "error" ? (
    <ErrorOutlineIcon color="error" fontSize="small" />
  ) : (
    <WarningAmberOutlinedIcon color="warning" fontSize="small" />
  );
}

export function RuleCheckPanel({ result, compact = false }: RuleCheckPanelProps) {
  const errors = result.issues.filter((issue) => issue.severity === "error").length;
  const warnings = result.issues.filter((issue) => issue.severity === "warning").length;
  const totals = Object.entries(result.totals);

  return (
    <Paper
      variant="outlined"
      sx={{
        p: compact ? 1.5 : 2,
        bgcolor: "background.paper",
      }}
    >
      <Stack spacing={1.5}>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={1}
          sx={{
            alignItems: { xs: "flex-start", sm: "center" },
            justifyContent: "space-between",
          }}
        >
          <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
            <CheckCircleOutlineIcon
              color={result.is_valid ? "success" : "disabled"}
              fontSize="small"
            />
            <Typography variant="h3">Rule Check</Typography>
          </Stack>
          <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
            <Chip
              label={result.is_valid ? "Valid" : "Needs changes"}
              color={result.is_valid ? "success" : "error"}
              size="small"
            />
            <Chip label={`${errors} errors`} color={errors ? "error" : "default"} size="small" />
            <Chip
              label={`${warnings} warnings`}
              color={warnings ? "warning" : "default"}
              size="small"
            />
          </Stack>
        </Stack>

        <Alert severity={result.is_valid ? "success" : "warning"} variant="outlined">
          {result.summary}
        </Alert>

        {totals.length > 0 && (
          <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
            {totals.map(([key, value]) => (
              <Chip key={key} label={`${formatKey(key)}: ${value}`} size="small" />
            ))}
          </Stack>
        )}

        {result.issues.length > 0 && (
          <Box>
            <Divider sx={{ mb: 1 }} />
            <List dense disablePadding>
              {result.issues.map((issue) => (
                <ListItem
                  key={`${issue.code}-${issue.message}`}
                  disableGutters
                  sx={{ alignItems: "flex-start", py: 0.75 }}
                >
                  <ListItemIcon sx={{ minWidth: 32, pt: 0.25 }}>
                    {issueIcon(issue)}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Stack
                        direction="row"
                        spacing={0.75}
                        sx={{ alignItems: "center", flexWrap: "wrap" }}
                      >
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                          {issue.message}
                        </Typography>
                        <Chip label={issue.code} size="small" variant="outlined" />
                      </Stack>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        )}
      </Stack>
    </Paper>
  );
}
