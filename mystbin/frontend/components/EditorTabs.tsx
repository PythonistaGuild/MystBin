import { useEffect, useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from "../styles/EditorTabs.module.css";
import { Toast } from "react-bootstrap";
import PasswordModal from "./PasswordModal";
import AES from "crypto-js/aes";
import Utf8 from "crypto-js/enc-utf8";
import Tab from "./Tab";
import NewTabButton from "./NewTabButton";

export default function EditorTabs({ initialData, encryptedPayload }) {
  const [value, setValue] = useState<Record<string, string>[]>(initialData);
  const [currTab, setCurrTab] = useState(0);
  const [charCountToast, setCharCountToast] = useState(false);
  const [passwordModal, setPasswordModal] = useState(!!encryptedPayload);
  const [shake, setShake] = useState(false);
  const [lang, setLang] = useState<string[]>([]);

  useEffect(() => {
    if (!value[currTab]) {
      let tabNumber = currTab.valueOf();
      console.log(tabNumber);
      if (currTab > 1) {
        tabNumber = currTab - 1;
      } else {
        tabNumber = 0;
      }

      setCurrTab(tabNumber);
    }
  }, [value]);

  useEffect(() => {
    let initialLangs = [];
    value.map(function (v) {
      if (v["title"].endsWith(".py")) {
        initialLangs.push("python");
      } else {
        initialLangs.push("none");
      }

      setLang(initialLangs);
    });
  }, [value]);

  const handlePasswordAttempt = (attempt: string) => {
    let decryptedBytes = AES.decrypt(encryptedPayload, attempt);
    try {
      let actualData = JSON.parse(decryptedBytes.toString(Utf8));
      setPasswordModal(false);
      setValue(actualData);
    } catch {
      setShake(true);
      setTimeout(function () {
        setShake(false);
      }, 500);
    }
  };

  return (
    <>
      <PasswordModal
        show={passwordModal}
        shake={shake}
        onAttempt={handlePasswordAttempt}
      />
      <div>
        <div className={styles.tabsContainer}>
          {value.map((v, i) => (
            <Tab
              key={i}
              current={currTab === i}
              deletable={value.length > 1}
              filename={v.title}
              onFocus={() => setCurrTab(i)}
              onChange={(filename) => {
                let newValue = [...value];
                newValue[i].title = filename;
                setValue(newValue);
              }}
              onDelete={() => {
                let newValue = [...value];
                newValue.splice(i, 1);
                setValue(newValue);
              }}
            />
          ))}
          <NewTabButton
            onClick={() => {
              let newValue = [...value];
              newValue.push({ title: "default_name.ext", content: "" });
              setValue(newValue);
              setCurrTab(value.length);
            }}
            enabled={value.length <= 4}
          />
        </div>

        {value.map((v, i) => (
          <div
            key={i}
            style={{
              display: currTab === i ? "block" : "none",
            }}
            className={"maxed"}
            id={`tab-${i}`}
          >
            <MonacoEditor
              language={lang[i]}
              onChange={(_, newVal) => {
                if (newVal.length > 300000) {
                  setCharCountToast(true);
                  newVal = newVal.slice(0, 300000);
                }
                let newValue = [...value];
                newValue[i]["content"] = newVal;
                setValue(newValue);
                return `${newVal}`;
              }}
              value={v.content}
              theme={"mystBinDark"}
              readOnly={false}
            />
          </div>
        ))}
      </div>

      <Toast
        className={styles.maxCountToast}
        onClose={() => setCharCountToast(false)}
        show={charCountToast}
        delay={5000}
        autohide
      >
        <Toast.Header className={styles.maxCountToastHeader}>
          <strong className="mr-auto">Max Character Count</strong>
          <small>Max count: 300,000</small>
        </Toast.Header>
        <Toast.Body>
          You've reached the max character count for this file.
        </Toast.Body>
      </Toast>
    </>
  );
}
