import React, { useState } from "react";
import styles from "../styles/Tab.module.css";
import CloseIcon from "@material-ui/icons/Close";

export default function Tab({
  current,
  onFocus,
  onChange,
  onDelete,
  initialFilename,
  deletable,
}: {
  current: boolean;
  onFocus: () => void;
  onChange: (arg0: string[]) => void;
  onDelete: () => void;
  initialFilename: string;
  deletable: boolean;
}) {
  const [filename, setFilename] = useState(initialFilename);
  const [lang, setLang] = useState("none");
  const spanRef = React.createRef<HTMLSpanElement>();

  return (
    <div className={current ? styles.tabsSelected : styles.tabs}>
      <div
        onClick={onFocus}
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

          setFilename(_filename);

          if (filename.endsWith(".py")) {
            setLang("python");
          } else {
            setLang("none");
          }

          onChange([filename, lang]);
        }}
      >
        <span
          ref={spanRef}
          contentEditable={true}
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
