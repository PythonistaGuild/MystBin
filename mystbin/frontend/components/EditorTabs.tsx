import { useEffect, useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from "../styles/EditorTabs.module.css";
import { Toast } from "react-bootstrap";
import PasswordModal from "./PasswordModal";
import Tab from "./Tab";
import NewTabButton from "./NewTabButton";
import pasteDispatcher from "../dispatchers/PasteDispatcher";
import getLanguage from "../stores/languageStore";
import config from "../config.json";

interface TabInfo {
  initialData?: any;
  hasPassword?: boolean;
  pid?: string;
}

export default function EditorTabs({
  initialData = null,
  hasPassword = false,
  pid = null,
}: TabInfo) {
  const [value, setValue] = useState<Record<string, string>[]>([
    { title: "file.txt", content: "" },
  ]);
  const [currTab, setCurrTab] = useState(0);
  const [charCountToast, setCharCountToast] = useState(false);
  const [passwordModal, setPasswordModal] = useState(!!hasPassword);
  const [shake, setShake] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState<string[]>([]);
  const id = pid;
  const [initialState, setInitialState] = useState(false);

  pasteDispatcher.dispatch({ paste: value });
  const maxCharCount = config["paste"]["character_limit"];

  if (initialData !== null && !initialState) {
    setValue(initialData);
    setInitialState(true);
  }

  useEffect(() => {
    if (sessionStorage.getItem("pasteCopy") !== null) {
      setValue(JSON.parse(sessionStorage.getItem("pasteCopy")));
    }
  }, []);

  useEffect(() => {
    if (!value[currTab]) {
      let tabNumber = currTab.valueOf();
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
      let filetype = v["title"].split(".").pop();
      let val = getLanguage(filetype);
      initialLangs.push(val);
      setLang(initialLangs);
    });
  }, [value]);

  const handlePasswordAttempt = async (attempt: string) => {
    setLoading(true);
    const response = await fetch(
      config["site"]["backend_site"] + "/paste/" + id + "?password=" + attempt,
      { headers: { Accept: "application/json" } }
    );
    const paste = await response.json();
    let actualData = [];

    try {
      if (response.status === 200) {
        setPasswordModal(false);

        for (let file of paste["pastes"]) {
          actualData.push({
            title: file["filename"],
            content: file["content"],
          });
        }
        setValue(actualData);
      } else {
        throw () => {};
      }
    } catch {
      setShake(true);
      setTimeout(function () {
        setShake(false);
      }, 500);
    }
    setLoading(false);
  };

  return (
    <>
      <PasswordModal
        show={passwordModal}
        shake={shake}
        loading={loading}
        onAttempt={handlePasswordAttempt}
      />

      <div>
        <div className={styles.tabsContainer}>
          {value.map((v, i) => (
            <Tab
              key={i}
              current={currTab === i}
              editable={!pid}
              deletable={value.length > 1 && !initialData}
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
            enabled={value.length <= 4 && !id}
          />
        </div>

        {value.map((v, i, arr) => (
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
                if (newVal.length > maxCharCount) {
                  setCharCountToast(true);
                  newVal = newVal.slice(0, maxCharCount);
                }
                let newValue = [...value];
                newValue[i]["content"] = newVal;
                setValue(newValue);
                return `${newVal}`;
              }}
              value={v.content}
              theme={"mystBinDark"}
              readOnly={!!id}
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
          <small>Max count: {{ maxCharCount }}</small>
        </Toast.Header>
        <Toast.Body>
          You've reached the max character count for this file.
        </Toast.Body>
      </Toast>
    </>
  );
}
