import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";

import type { Citation } from "@/types/api";

type CitationListProps = {
  citations: Citation[];
};

function citationTitle(citation: Citation) {
  return citation.title ?? citation.section_heading ?? citation.source;
}

function isCourseOfferingCitation(citation: Citation) {
  const heading = citation.section_heading ?? "";
  const isLookupBucket = /^[^/]+\/[^/]+\/[^/]+$/.test(heading);
  return citation.source.includes("course_offerings/") || isLookupBucket;
}

export function CitationList({ citations }: CitationListProps) {
  const visibleCitations = citations.filter((citation) => !isCourseOfferingCitation(citation));

  if (visibleCitations.length === 0) {
    return null;
  }

  return (
    <Box sx={{ mt: 1.5 }}>
      <Typography
        variant="caption"
        sx={{ color: "text.secondary", fontWeight: 700, display: "block", mb: 0.75 }}
      >
        Citations
      </Typography>
      <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
        {visibleCitations.map((citation, index) => {
          const labelParts = [
            citationTitle(citation),
            citation.page ? `p. ${citation.page}` : null,
          ].filter(Boolean);

          return (
            <Tooltip
              key={`${citation.source}-${citation.page ?? "page"}-${index}`}
              title={citation.source}
            >
              <Chip
                icon={<DescriptionOutlinedIcon />}
                label={labelParts.join(" - ")}
                size="small"
                variant="outlined"
                sx={{ maxWidth: 360 }}
              />
            </Tooltip>
          );
        })}
      </Stack>
    </Box>
  );
}
