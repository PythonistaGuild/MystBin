import { PropsWithChildren } from "react";
import OptsBar from "./OptsBar";
import styles from "../styles/Base.module.css";
import LogoMain from "../public/LogoMain";
import GitHubIcon from "@material-ui/icons/GitHub";
import DiscordColorIcon from "../icons/DiscordColour";

export default function Base(props: PropsWithChildren<{ className: string }>) {
  const { children, className } = props;

  return (
    <div className={styles.Base}>
      <OptsBar />
      <main className={className}>{children}</main>

      <div className={styles.footerContainer}>
        <span className={styles.footerTermsContainer}>
          <a className={styles.footerTerms}>Terms and Conditions</a>
          <span className={styles.footerTerms}>/</span>
          <a className={styles.footerTerms}>Privacy Policy</a>
          <span className={styles.footerTerms}>/</span>
          <a className={styles.footerTerms}>Contact Us</a>
        </span>

        <div className={styles.footerFlexCol}>
          <LogoMain className={styles.logo} />
          <p className={styles.footerLeft}>Copyright © 2020 PythonistaGuild</p>
        </div>

        <div className={styles.socialIconsContainer}>
          <a href="https://github.com/PythonistaGuild/MystBin">
            <GitHubIcon className={styles.socialIcon} />
          </a>
          <a href="https://discord.gg/RAKc3HF">
            <DiscordColorIcon className={styles.socialIcon} />
          </a>
        </div>
      </div>
    </div>
  );
}
