import { PropsWithChildren } from "react";
import NavBar from "./NavBar";
import OptsBar from "./OptsBar";
import styles from "../styles/Base.module.css";

export default function Base(props: PropsWithChildren<{ className: string }>) {
  const { children, className } = props;

  return (
    <div className={styles.Base}>
      <nav>
        <NavBar />
      </nav>
        <opts>
            <OptsBar />
        </opts>
      <main className={className}>{children}</main>
      <footer></footer>
    </div>
  );
}
