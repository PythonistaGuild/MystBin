import { PropsWithoutRef, useState } from "react";
import MonacoEditor from "./MonacoEditor";
import styles from "../styles/EditorTabs.module.css";
import CloseIcon from "@material-ui/icons/Close";
import LockIcon from "@material-ui/icons/Lock";
import Toast from "react-bootstrap/Toast";
import { Form, Modal } from "react-bootstrap";
import Link from "next/link";

export default function EditorTabs({ password, initialData, dummyData }) {
  const [value, setValue] = useState(initialData);
  const [currTab, setCurrTab] = useState(0);
  const [lang, setLang] = useState(Array(5).fill("none"));
  const [charCountToast, setCharCountToast] = useState(false);
  const [passwordModal, setPasswordModal] = useState(true);

  return (
    <>
      <Modal
        show={passwordModal}
        backdrop="static"
        keyboard={false}
        aria-labelledby="contained-modal-title-vcenter"
        centered
        className={styles.passwordModal}
      >
        <Modal.Header className={styles.passwordModalHeader}>
          <Modal.Title
            id={"contained-modal-title-vcenter"}
            className={styles.passwordModalTitle}
          >
            Password Protected
            <LockIcon />
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          This paste is password protected. Please enter the password to
          continue.
          <Form>
            <Form.Group controlId="pastePassword">
              <Form.Control
                type="password"
                placeholder="Password"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                  }
                }}
                onChange={(e) => {
                  if (e.currentTarget.value === password) {
                    setPasswordModal(false);

                    setValue(dummyData);
                  }
                }}
              />
            </Form.Group>
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Link href={"/"}>Return to home</Link>
        </Modal.Footer>
      </Modal>
      <div>
        <div className={styles.tabsContainer}>
          {value.map((v, i) => (
            <div className={currTab === i ? styles.tabsSelected : styles.tabs}>
              <div
                onClick={() => setCurrTab(i)}
                onKeyDown={(e) => {
                  const button = e.currentTarget;

                  if (e.key == "Enter") {
                    button.blur(); // Lose focus...
                  }
                }}
                onBlur={(e) => {
                  const filename = e.currentTarget.children[0];

                  if (filename.textContent === "") {
                    filename.textContent = `default_name.ext`;
                  }

                  let newValue = value;
                  newValue[i]["title"] = filename.textContent;
                  setValue(newValue);

                  if (filename.textContent.endsWith(".py")) {
                    let langCopy = [...lang];
                    langCopy[currTab] = "python";

                    setLang(langCopy);
                  }
                }}
              >
                <span
                  contentEditable={true}
                  className={styles.tabsFilename}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      e.currentTarget.blur();
                    }
                  }}
                >
                  {value[i]["title"]}
                </span>
              </div>
              {value.length > 1 ? (
                <button
                  className={styles.tabsCloseButton}
                  onClick={(event) => {
                    let newValue = [...value];
                    let newLang = [...lang];

                    newValue.splice(i, 1);
                    newLang.splice(i, 1);
                    newLang.push("none");

                    setCurrTab(
                      currTab > 1 ? (currTab !== i ? currTab : currTab - 1) : 0
                    );

                    setLang(newLang);
                    setValue(newValue);
                  }}
                >
                  <CloseIcon className={styles.tabsCloseButton} />
                </button>
              ) : (
                <></>
              )}
            </div>
          ))}
          {value.length <= 4 ? (
            <button
              className={styles.tabsNew}
              onClick={() => {
                if (value.length <= 4) {
                  let newValue = [...value];
                  newValue.push({ title: "default_name.ext", content: "" });
                  setValue(newValue);
                  setCurrTab(value.length);
                }
              }}
            >
              +
            </button>
          ) : (
            <></>
          )}
        </div>

        {value.map((v, i) => (
          <div
            style={{
              display: currTab === i ? "block" : "none",
            }}
            className={"maxed"}
          >
            <MonacoEditor
              language={lang[i]}
              onChange={(ev, newVal) => {
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
