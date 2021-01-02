import React, { useState } from "react";
import styles from "../styles/Tab.module.css";
import CloseIcon from "@material-ui/icons/Close";

export default function Tab({
  current,
  onFocus,
  onChange,
  onDelete,
  filename,
  deletable,
}: {
  current: boolean;
  onFocus: () => void;
  onChange: (arg0: string[]) => void;
  onDelete: () => void;
  filename: string;
  deletable: boolean;
}) {
  const [lang, setLang] = useState("none");
  const spanRef = React.createRef<HTMLSpanElement>();

  return (
    <div
      onClick={onFocus}
      className={current ? styles.tabsSelected : styles.tabs}
    >
      <div
        onKeyDown={(e) => {
          const button = e.currentTarget;

          if (e.key == "Enter") {
            button.blur(); // Lose focus...
          }
        }}
        onBlur={() => {
          let _filename = spanRef.current.textContent;

          if (_filename === "") {
            _filename = filename;
          }

          if (filename.endsWith(".py")) {
            setLang("python");
          } else {
            setLang("none");
          }

          onChange([_filename, lang]);
        }}
      >
        <span
          ref={spanRef}
          contentEditable={current}
          className={styles.tabsFilename}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              e.currentTarget.blur();
            }
          }}
        >
          {filename}
        </span>
      </div>
      {deletable && (
        <button className={styles.tabsCloseButton} onClick={onDelete}>
          <CloseIcon className={styles.tabsCloseButton} />
        </button>
      )}
    </div>
  );
}
