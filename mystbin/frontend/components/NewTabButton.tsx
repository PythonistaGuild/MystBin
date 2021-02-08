import styles from "../styles/NewTabButton.module.css";

export default function NewTabButton({ enabled, onClick }) {
  return (
    enabled && (
      <button className={styles.tabsNew} onClick={onClick}>
        +
      </button>
    )
  );
}
