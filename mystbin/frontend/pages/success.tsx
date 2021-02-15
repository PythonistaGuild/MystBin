import styles from "../styles/Success.module.css";
import Image from "next/image";

export default function success() {
  return (
    <div>
      <div className={styles.successImage}>
        <Image src={"/success.gif"} height={"300px"} width={"500px"} /><br />
        You may close this window
      </div>
    </div>
  );
}