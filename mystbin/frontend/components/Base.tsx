import { PropsWithChildren } from "react";
import OptsBar from "./OptsBar";
import styles from "../styles/Base.module.css";
import LogoMain from "../public/LogoMain";
import GitHubIcon from "@material-ui/icons/GitHub";
import DiscordColorIcon from "../icons/DiscordColour";
import PatreonFireyIcon from "../icons/PatreonFirey";

export default function Base(props: PropsWithChildren<{ className: string }>) {
  const { children, className } = props;

  return (
    <div className={styles.Base}>
      <OptsBar />
      <main className={className}>{children}</main>
      <footer>
        <span className={styles.footerLeft}>Copyright © 2021 PythonistaGuild</span>
        <LogoMain className={styles.logo} />
        <div className={styles.socialIconsContainer}>
            <GitHubIcon className={styles.socialIcon} />
            <DiscordColorIcon className={styles.socialIcon} />
            <PatreonFireyIcon className={styles.socialIcon} />
        </div>
      </footer>
    </div>
  );
}
