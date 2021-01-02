import { PropsWithChildren } from "react";
import OptsBar from "./OptsBar";
import styles from "../styles/Base.module.css";
import LogoMain from "../public/LogoMain";

export default function Base(props: PropsWithChildren<{ className: string }>) {
  const { children, className } = props;

  return (
    <div className={styles.Base}>
      <OptsBar />
      <main className={className}>{children}</main>
      <footer>
        <LogoMain className={styles.logo} />
      </footer>
    </div>
  );
}
