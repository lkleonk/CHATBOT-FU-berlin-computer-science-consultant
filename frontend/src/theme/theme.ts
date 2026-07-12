import { alpha, createTheme } from "@mui/material/styles";

import { colors } from "./colors";

export function createAppTheme(darkMode: boolean) {
  const primary = darkMode
    ? {
        main: "#78d6b4",
        dark: "#43ad86",
        light: "#b8f1da",
        contrastText: "#10221b",
      }
    : {
        main: colors.fuGreen,
        dark: colors.fuGreenDark,
        light: colors.fuGreenLight,
      };

  return createTheme({
    palette: {
      mode: darkMode ? "dark" : "light",
      primary,
      secondary: {
        main: colors.info,
      },
      success: {
        main: colors.success,
      },
      warning: {
        main: colors.warning,
      },
      error: {
        main: colors.danger,
      },
      background: {
        default: darkMode ? "#111816" : colors.paperMuted,
        paper: darkMode ? "#17211e" : colors.paper,
      },
      divider: darkMode ? alpha("#ffffff", 0.12) : colors.border,
      text: {
        primary: darkMode ? "#eef4f1" : colors.ink,
        secondary: darkMode ? "#b8c7c1" : "#52615c",
      },
    },
    shape: {
      borderRadius: 6,
    },
    typography: {
      fontFamily:
        'Arial, "Helvetica Neue", Helvetica, system-ui, -apple-system, BlinkMacSystemFont, sans-serif',
      h1: {
        fontSize: "1.55rem",
        fontWeight: 700,
        letterSpacing: 0,
      },
      h2: {
        fontSize: "1.25rem",
        fontWeight: 700,
        letterSpacing: 0,
      },
      h3: {
        fontSize: "1rem",
        fontWeight: 700,
        letterSpacing: 0,
      },
      button: {
        textTransform: "none",
        fontWeight: 700,
        letterSpacing: 0,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 6,
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          switchBase: {
            "&.Mui-checked": {
              color: darkMode ? "#b8f1da" : colors.fuGreen,
            },
            "&.Mui-checked + .MuiSwitch-track": {
              backgroundColor: darkMode ? "#43ad86" : colors.fuGreen,
              opacity: 1,
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 8,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 6,
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            minHeight: 52,
            letterSpacing: 0,
            textTransform: "none",
          },
        },
      },
      MuiTextField: {
        defaultProps: {
          variant: "outlined",
        },
      },
    },
  });
}
