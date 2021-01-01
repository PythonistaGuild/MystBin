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
  const [tabs, setTabs] = useState<React.ElementType[]>([]);

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

  useEffect(() => {
    let newTabs = [];
    value.forEach((v, i) => {
      newTabs.push(
        <Tab
          current={currTab === i}
          deletable={value.length > 1}
          initialFilename={v.title || "default_name.ext"}
          onFocus={() => setCurrTab(i)}
          onChange={([filename, _lang]) => {
            let newValue = [...value];
            newValue[i].title = filename;

            let newLang = [...lang];
            newLang[i] = _lang;

            setValue(newValue);
            setLang(newLang);
          }}
          onDelete={() => {
            let newValue = [...value];
            let newLang = [...lang];

            newValue.splice(i, 1);
            newLang.splice(i, 1);
            newLang.push("none");
            let tabNumber = currTab;

            if (currTab > 1) {
              if (currTab === i) {
                tabNumber = currTab - 1;
              } else {
                tabNumber = currTab - 1;
              }
            } else {
              tabNumber = 0;
            }

            setCurrTab(tabNumber);
            setTabs([]);
            setLang(newLang);
            setValue(newValue);
          }}
        />
      );
      setTabs(newTabs);
    });
  }, [value]);

  const handlePasswordAttempt = (attempt: string) => {
    let decryptedBytes = AES.decrypt(encryptedPayload, attempt);
    try {
      let actualData = JSON.parse(decryptedBytes.toString(Utf8));
      setPasswordModal(false);
      setValue(actualData);
      setTabs([]);
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
          {tabs.map((v) => v)}
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

        {value.map((_, i) => (
          <div
            style={{
              display: currTab === i ? "block" : "none",
            }}
            className={"maxed"}
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
              value={value[i]["content"]}
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
