import { useTranslation } from "react-i18next";
import { Card } from "#/ui/card";
import { CardTitle } from "#/ui/card-title";
import { Typography } from "#/ui/typography";
import { cn } from "#/utils/utils";
import { I18nKey } from "#/i18n/declaration";
import CloseIcon from "#/icons/close.svg?react";

interface HomepageCTAProps {
  onClose?: () => void;
}

export function HomepageCTA({ onClose }: HomepageCTAProps) {
  const { t } = useTranslation();

  return (
    <Card
      border="none"
      className={cn(
        "w-[320px] h-[222px] rounded-2xl border border-[#24242499] bg-black relative",
        "bg-[radial-gradient(85.36%_123.38%_at_50%_0%,rgba(255,255,255,0.14)_0%,rgba(0,0,0,0)_100%)]",
        "shadow-[0px_4px_6px_-4px_#0000001A,0px_10px_15px_-3px_#0000001A]",
      )}
    >
      <button
        type="button"
        onClick={onClose}
        className="absolute top-[13px] left-[279px] w-7 h-7 rounded-full border border-[#242424] bg-[#0A0A0A] flex items-center justify-center text-white/60 hover:text-white cursor-pointer shadow-[0px_1px_2px_-1px_#0000001A,0px_1px_3px_0px_#0000001A]"
        aria-label="Close"
      >
        <CloseIcon width={16} height={16} />
      </button>

      <div className="w-[270px] h-[180px] mt-[21px] ml-[25px] flex flex-col gap-4">
        <div className="w-[270px] flex flex-col gap-2">
          <CardTitle className="font-inter font-semibold text-xl leading-7 tracking-normal max-w-[186px]">
            {t(I18nKey.CTA$ENTERPRISE_TITLE)}
          </CardTitle>

          <Typography.Text className="font-inter font-normal text-sm leading-5 tracking-normal text-white/60 max-w-[270px] max-h-[60px]">
            {t(I18nKey.CTA$ENTERPRISE_DESCRIPTION)}
          </Typography.Text>
        </div>

        <button
          type="button"
          className="max-w-[111px] h-10 rounded border border-[#242424] bg-[#050505] text-white text-sm font-medium px-4 py-2 hover:bg-[#1a1a1a] cursor-pointer"
        >
          {t(I18nKey.CTA$LEARN_MORE)}
        </button>
      </div>
    </Card>
  );
}
