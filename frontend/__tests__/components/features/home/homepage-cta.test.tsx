import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { HomepageCTA } from "#/components/features/home/homepage-cta";

// Mock the translation function
vi.mock("react-i18next", async () => {
  const actual = await vi.importActual("react-i18next");
  return {
    ...actual,
    useTranslation: () => ({
      t: (key: string) => {
        const translations: Record<string, string> = {
          "CTA$ENTERPRISE_TITLE": "Get OpenHands for Enterprise",
          "CTA$ENTERPRISE_DESCRIPTION":
            "Cloud allows you to access OpenHands anywhere and coordinate with your team like never before",
          "CTA$LEARN_MORE": "Learn More",
        };
        return translations[key] || key;
      },
      i18n: { language: "en" },
    }),
  };
});

// Mock session storage
vi.mock("#/utils/session-storage", () => ({
  setCTADismissed: vi.fn(),
}));

import { setCTADismissed } from "#/utils/session-storage";

describe("HomepageCTA", () => {
  const mockSetShouldShowCTA = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderHomepageCTA = () => {
    return render(<HomepageCTA setShouldShowCTA={mockSetShouldShowCTA} />);
  };

  describe("rendering", () => {
    it("renders the enterprise title", () => {
      renderHomepageCTA();
      expect(screen.getByText("Get OpenHands for Enterprise")).toBeInTheDocument();
    });

    it("renders the enterprise description", () => {
      renderHomepageCTA();
      expect(
        screen.getByText(/Cloud allows you to access OpenHands anywhere/),
      ).toBeInTheDocument();
    });

    it("renders the Learn More button", () => {
      renderHomepageCTA();
      expect(screen.getByText("Learn More")).toBeInTheDocument();
    });

    it("renders the close button with correct aria-label", () => {
      renderHomepageCTA();
      expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
    });
  });

  describe("close button behavior", () => {
    it("calls setCTADismissed with 'homepage' when close button is clicked", async () => {
      const user = userEvent.setup();
      renderHomepageCTA();

      const closeButton = screen.getByRole("button", { name: "Close" });
      await user.click(closeButton);

      expect(setCTADismissed).toHaveBeenCalledWith("homepage");
    });

    it("calls setShouldShowCTA with false when close button is clicked", async () => {
      const user = userEvent.setup();
      renderHomepageCTA();

      const closeButton = screen.getByRole("button", { name: "Close" });
      await user.click(closeButton);

      expect(mockSetShouldShowCTA).toHaveBeenCalledWith(false);
    });

    it("calls both setCTADismissed and setShouldShowCTA in order", async () => {
      const user = userEvent.setup();
      const callOrder: string[] = [];
      
      vi.mocked(setCTADismissed).mockImplementation(() => {
        callOrder.push("setCTADismissed");
      });
      mockSetShouldShowCTA.mockImplementation(() => {
        callOrder.push("setShouldShowCTA");
      });

      renderHomepageCTA();

      const closeButton = screen.getByRole("button", { name: "Close" });
      await user.click(closeButton);

      expect(callOrder).toEqual(["setCTADismissed", "setShouldShowCTA"]);
    });
  });

  describe("accessibility", () => {
    it("close button is focusable", () => {
      renderHomepageCTA();
      const closeButton = screen.getByRole("button", { name: "Close" });
      expect(closeButton).not.toHaveAttribute("tabindex", "-1");
    });

    it("Learn More button is a button element", () => {
      renderHomepageCTA();
      const learnMoreButton = screen.getByRole("button", { name: "Learn More" });
      expect(learnMoreButton).toBeInTheDocument();
      expect(learnMoreButton.tagName).toBe("BUTTON");
    });
  });
});
