import { PropsWithChildren } from "react";
import OptsBar from "./OptsBar";
import styles from "../styles/Base.module.css";
import LogoMain from "../public/LogoMain";
import GitHubIcon from "@material-ui/icons/GitHub";
import DiscordColorIcon from "../icons/DiscordColour";
import TipModal from "./TipModal";
import Head from "next/head";

export default function Base(props: PropsWithChildren<{ className: string }>) {
  const { children, className } = props;

  return (
    <div className={styles.Base}>
      <div
        data-ea-publisher="mystbin"
        data-ea-type="text"
        data-ea-style="fixedfooter"
      ></div>

      <OptsBar />
      <TipModal />
      <main className={className}>{children}</main>

      <div className={styles.footerContainer}>
        <div className={styles.footerFlexRow}>
          <LogoMain className={styles.logo} />
          <span className={styles.footerLeft}>
            Copyright © 2020-current PythonistaGuild
          </span>
        </div>

        <div className={styles.socialIconsContainer}>
          <a href="https://github.com/PythonistaGuild/MystBin">
            <GitHubIcon className={styles.socialIconGH} />
          </a>
          <a href="https://discord.gg/RAKc3HF">
            <DiscordColorIcon className={styles.socialIcon} />
          </a>
        </div>

        <span className={styles.footerTermsContainer}>
          <a className={styles.footerTerms}>Terms and Conditions</a>
          <span className={styles.footerTerms}>/</span>
          <a className={styles.footerTerms}>Privacy Policy</a>
          <span className={styles.footerTerms}>/</span>
          <a className={styles.footerTerms}>Contact Us</a>
        </span>
      </div>
    </div>
  );
}
