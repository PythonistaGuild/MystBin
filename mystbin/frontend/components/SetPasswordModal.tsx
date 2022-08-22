import { useState } from "react";
import { Button, Form, InputGroup, Modal } from "react-bootstrap";
import styles from "../styles/PasswordModal.module.css";
import PasswordInput from "./PasswordInput";
import pasteStore from "../stores/PasteStore";
import pasteDispatcher from "../dispatchers/PasteDispatcher";

export default function SetPasswordModal({ onHide }: { onHide: () => void }) {
  const [passwordValue, setPasswordValue] = useState("");
  const [passwordTwoValue, setPasswordTwoValue] = useState("");
  const [passwordsMatch, setPasswordsMatch] = useState(true);

  const handlePasswordSubmit = (e) => {
    e.preventDefault();

    if (passwordValue != passwordTwoValue) {
      setPasswordsMatch(false);
      return;
    }

    onHide();

    const paste = pasteStore.getPaste();
    paste.password = passwordValue;

    pasteDispatcher.dispatch({ paste: paste });
  };

  return (
    <Modal
      show={true}
      onHide={onHide}
      aria-labelledby="contained-modal-title-vcenter"
      centered={true}
      className={styles.passwordModal}
    >
      <Modal.Header className={styles.passwordModalHeader}>
        <Modal.Title className={styles.passwordModalTitle}>
          Set the paste Password
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Form
          style={{
            justifyContent: "flex-start",
            display: "flex",
            flexDirection: "column",
          }}
          onSubmit={handlePasswordSubmit}
        >
          {passwordsMatch ? null : (
            <span style={{ color: "red" }}>
              Your passwords do not match! Please make sure the passwords are
              the same.
              <br />
            </span>
          )}
          Enter your password:
          <PasswordInput
            value={passwordValue}
            onChange={setPasswordValue}
            onSubmit={handlePasswordSubmit}
          />
          <br />
          Re-enter your password:
          <PasswordInput
            value={passwordTwoValue}
            onChange={setPasswordTwoValue}
            onSubmit={() => {}}
          />
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="info" type="submit" onClick={handlePasswordSubmit}>
          Set Password
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
