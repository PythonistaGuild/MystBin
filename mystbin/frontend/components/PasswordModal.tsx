import LockIcon from "@material-ui/icons/Lock";
import { Button, Form, Modal } from "react-bootstrap";
import Link from "next/link";
import styles from "../styles/EditorTabs.module.css";
import { useState } from "react";

export default function PasswordModal({
  show,
  shake,
  onAttempt,
}: {
  show: boolean;
  shake: boolean;
  onAttempt: (arg0: string) => void;
}) {
  let [passwordAttempt, setPasswordAttempt] = useState("");

  return (
    <Modal
      show={show}
      backdrop="static"
      keyboard={false}
      aria-labelledby="contained-modal-title-vcenter"
      centered
      className={styles.passwordModal + " " + (shake && styles.shakeModal)}
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
        This paste is password protected. Please enter the password to continue.
        <Form>
          <Form.Group controlId="pastePassword">
            <Form.Control
              type="password"
              placeholder="Password"
              onChange={(event) => {
                setPasswordAttempt(event.currentTarget.value);
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  onAttempt(passwordAttempt);
                }
              }}
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Link href={"/"}>Return to home</Link>
        <Button
          variant="info"
          type="submit"
          onClick={() => onAttempt(passwordAttempt)}
        >
          Submit
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
