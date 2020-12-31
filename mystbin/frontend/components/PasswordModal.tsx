import LockIcon from "@material-ui/icons/Lock";
import { Button, Modal } from "react-bootstrap";
import Link from "next/link";
import styles from "../styles/PasswordModal.module.css";
import { useState } from "react";
import PasswordInput from "./PasswordInput";

export default function PasswordModal({
  show,
  shake,
  onAttempt,
}: {
  show: boolean;
  shake: boolean;
  onAttempt: (arg0: string) => void;
}) {
  const [passwordAttempt, setPasswordAttempt] = useState("");

  return (
    <Modal
      show={show}
      backdrop="static"
      keyboard={false}
      aria-labelledby="contained-modal-title-vcenter"
      centered
      className={styles.passwordModal}
      style={
        shake
          ? {
              animation: "shake 0.5s",
              animationIterationCount: 1,
            }
          : {}
      }
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
        <PasswordInput
          value={passwordAttempt}
          onChange={setPasswordAttempt}
          onSubmit={onAttempt}
        />
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
