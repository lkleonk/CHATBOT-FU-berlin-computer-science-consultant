import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogTitle from "@mui/material/DialogTitle";

type ChatErrorDialogProps = {
  open: boolean;
  message: string;
  onClose: () => void;
};

export const DEFAULT_CHAT_ERROR_MESSAGE =
  "The consultant could not generate an answer right now. Please try again.";

export function ChatErrorDialog({ open, message, onClose }: ChatErrorDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="xs" aria-labelledby="chat-error-title">
      <DialogTitle id="chat-error-title">No answer received</DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
        <DialogContentText sx={{ mt: 1.25 }}>
          We couldn't get a response this time. Please try again in a moment.
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} autoFocus>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}
