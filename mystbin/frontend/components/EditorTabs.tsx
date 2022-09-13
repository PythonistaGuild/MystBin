import { useEffect, useRef, useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from "../styles/EditorTabs.module.css";
import {Dropdown, Toast, ToastHeader} from "react-bootstrap";
import PasswordModal from "./PasswordModal";
import Tab from "./Tab";
import NewTabButton from "./NewTabButton";
import pasteDispatcher from "../dispatchers/PasteDispatcher";
import getLanguage from "../stores/languageStore";
import config from "../config.json";
import { Button } from "@material-ui/core";
import DropdownItem from "react-bootstrap/DropdownItem";
import React from "react";
import SettingsIcon from "@material-ui/icons/Settings";
import AddBoxIcon from '@material-ui/icons/AddBox';
import LibraryAddCheckIcon from '@material-ui/icons/LibraryAddCheck';
import {ImageRounded} from "@material-ui/icons";

const languages = {
  py: "python",
  python: "python",
  pyi: "python",
  js: "javascript",
  javascript: "javascript",
  jsx: "javascript",
  ts: "typescript",
  typescript: "typescript",
  tsx: "typescript",
  html: "html",
  swift: "swift",
  json: "json",
  rs: "rust",
  rust: "rust",
  ex: "elixir",
  elixir: "elixir",
  md: "markdown",
  markdown: "markdown",
  go: "go",
  cpp: "cpp",
  c: "cpp",
  h: "cpp",
  cs: "csharp",
  css: "css",
  hs: "haskell",
  perl: "perl",
  pl: "perl",
  pm: "perl",
  bash: "bash",
  zsh: "bash",
  sh: "bash",
  sql: "sql",
  nginx: "nginx",
  ini: "ini",
  toml: "toml",
  xml: "xml",
  yml: "yml",
  yaml: "yml",
};

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
  const [value, setValue] = useState([{ title: "file.txt", content: "", image: "" },]);
  const [currTab, setCurrTab] = useState(0);
  const [charCountToast, setCharCountToast] = useState(false);
  const [passwordModal, setPasswordModal] = useState(!!hasPassword);
  const [shake, setShake] = useState(false);
  const [loading, setLoading] = useState(false);
  const [lang, setLang] = useState<string[]>([]);
  const id = pid;
  const [initialState, setInitialState] = useState(false);
  const [langDropDown, setLangDropDown] = useState(false);
  const [dropLang, setDropLang] = useState(null);
  const [image, setImage] = useState(null)
  const [showImage, setShowImage] = useState(null)

  const tabRef = useRef();
  const imageRef = useRef();
  const DnDRef = useRef();

  async function handleDnD(e, index) {
    e.preventDefault()

    if (!!id) {
      return;
    }

    if(e.dataTransfer && e.dataTransfer.files.length != 0) {
      let file = e.dataTransfer.files[0]

      if (file.size / 1024 / 1024 > 4) {
        alert('You can only upload files 4Mb in size or less.');
        return;

      }

      let data = await file.text();
      let name = file.name;

      let newValue = [...value];
      newValue[index]['title'] = name;
      newValue[index]['content'] = data;

      setValue(newValue);
    }

  }


  function handleSetImage(e) {
    let file = e.currentTarget.files[0]
    let allowed = ['image/gif', 'image/jpeg', 'image/png'];

    if (!!file && !allowed.includes(file['type'])) {
      alert('Only images are currently supported.')
    }
    else if (file.size / 1024 / 1024 > 4) {
      alert('You can only upload files 4Mb in size or less.')
    }
    else {
      setImage(file)
    }
  }

  useEffect( () => {
    let newValue = [...value];
    newValue[currTab]['image'] = image

    setValue(newValue)
  }, [image])

  pasteDispatcher.dispatch({ paste: value });
  const maxCharCount = config["paste"]["character_limit"];

  useEffect( () => {
    if (initialData !== null && !initialState) {
      setValue(initialData);
      setInitialState(true);
    }
  }, [])

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
    let newLang = [...lang];
    newLang.splice(currTab, 1, dropLang);
    setLang(newLang);
  }, [langDropDown]);

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

        for (let file of paste["files"]) {
          actualData.push({
            title: file["filename"],
            content: file["content"],
            image: file['attachment']
          });
        }
        setValue(actualData);
        setPasswordModal(false);
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
      <div>
      {value.map((v, i) => (
          <div className={styles.attachmentImageBackdrop} onClick={(e) => setShowImage(-1)} style={{ display: showImage === i ? "flex" : "none",}}>
            <img className={styles.attachmentImage} src={value[i]['image']} style={{ display: showImage === i ? "block" : "none",}}/>
            <a className={styles.attachmentLink} href={value[i]['image']} target={"_blank"}>Open Original</a>
          </div>
        ))}
      </div>

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
            >
              <input ref={imageRef} type="file" style={{display: 'none'}} onChange={e => (handleSetImage(e))} />
              {!pid && value[i]['image'] === null || value[i]['image'] === "" ?
              <div className={styles.addImageButtonContainer} onClick={(e) => {
              e.preventDefault();
              // @ts-ignore
                imageRef.current.click();

            }} >
                <AddBoxIcon className={styles.addImagesButtonNS} ></AddBoxIcon>
              </div> : null}

              { value[i]['image'] !== 'None' && value[i]['image'] !== null && value[i]['image'] !== undefined && value[i]['image'] !== "" ?
                  <div
                      className={styles.addImageButtonContainer}
                      onClick={() => setShowImage(i)}
                  >
                    <ImageRounded className={styles.addImagesButtonNS}/>
                  </div>
                  : null }

              {!!pid ? (
                <div className={styles.dropdownContainer} ref={tabRef}>
                  <div
                    className={styles.langButton}
                    onClick={() => setLangDropDown(!langDropDown)}
                  >
                    <SettingsIcon />
                  </div>
                  {langDropDown && i === currTab ? (
                    <div className={styles.langParent}>
                      <Dropdown className={styles.dropDown} autoClose>
                        {Object.keys(languages).map((v, index) => {
                          return (
                            <DropdownItem
                              key={v}
                              className={styles.dropdownItem}
                              onBlur={(e) => {
                                e.preventDefault();
                              }}
                              onClick={() => {
                                setLangDropDown(false);
                                setDropLang(getLanguage(v));
                              }}
                            >
                              {v}
                            </DropdownItem>
                          );
                        })}
                      </Dropdown>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </Tab>
          ))}
          <NewTabButton
            onClick={() => {
              let newValue = [...value];
              newValue.push({ title: "file.txt", content: "", image: "" });
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
            <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={async (e) => await handleDnD(e, i)}
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
          </div>
        ))}
      </div>
    </>
  );
}
