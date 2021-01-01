import {Modal, Nav, Navbar, OverlayTrigger, Popover, Form, InputGroup, Button} from "react-bootstrap";
import React, { useState } from "react";
import EnhancedEncryptionIcon from "@material-ui/icons/EnhancedEncryption";
import HourglassFullIcon from "@material-ui/icons/HourglassFull";
import SaveAltIcon from "@material-ui/icons/SaveAlt";
import EditIcon from "@material-ui/icons/Edit";
import styles from "../styles/OptsBar.module.css";
import { useHotkeys } from "react-hotkeys-hook";

export default function OptsBar() {
  const [showExpiryModal, setShowExpiryModal] = useState(false);
  const [expiryValue, setExpiryValue] = useState([-1, -1, -1]);

  let days = [-1];
  let hours = [-1]
  const minutes = [-1, 0, 5, 15, 30, 45];

  for (let i=0; i <= 31; i++) {
    days.push(i);
  }

  for (let i=0; i <= 23; i++) {
    hours.push(i);
  }

  const handleExpirySubmit = e => {
    e.preventDefault();
    setShowExpiryModal(false);
    console.log(expiryValue);
  }

  const actions = [
    {
      title: "Save Paste",
      content: "Save this paste and all its files.",
      icon: <SaveAltIcon />,
      callback: () => {
        alert("test!");
      },
      hotKey: "ctrl+s",
    },
    {
      title: "Edit Paste",
      content: "Copy and Edit this paste as a new paste.",
      icon: <EditIcon />,
      callback: () => {
        alert("test2!");
      },
      hotKey: "ctrl+e",
    },
  ];

  const opts = [
    {
      title: "Create Password",
      content: "Create a password for this paste and all its files.",
      optional: true,
      icon: <EnhancedEncryptionIcon />,
      callback: () => alert("test3"),
    },
    {
      title: "Create Expiry",
      content: "Create a expiry date for this paste and all its files.",
      optional: true,
      icon: <HourglassFullIcon />,
      callback: () => setShowExpiryModal(true),
    },
  ];

  actions.forEach(({ callback, hotKey }) => {
    useHotkeys(hotKey, callback);
  });

  return (
    <div>
      <Modal
        show={showExpiryModal}
        onHide={() => setShowExpiryModal(false)}
        keyboard={false}
        aria-labelledby="contained-modal-title-vcenter"
        centered
        className={styles.expiryModal}
      >
        <Modal.Header className={styles.expiryModalHeader}>
          <Modal.Title className={styles.expiryModalTitle}>
            Set Paste Expiry
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <InputGroup className={'mb-3'} onSubmit={handleExpirySubmit}>

            <span className={styles.expiryModalLabel}>Days</span>
            <Form.Control
                as={"select"}
                onChange={(e) => {
                  const oldExpiry = expiryValue;
                  oldExpiry[0] = parseInt(e.target.value);

                  setExpiryValue(oldExpiry);
                }}>
              {days.map((v, i) => {
                if (v === -1 && expiryValue[0] === -1) {
                  return <option value={"Days"}>{"Days"}</option>
                }
                else if (v === -1 && expiryValue[0] !== -1) {
                  days.splice(days.indexOf(expiryValue[0]), 1);
                  return <option value={expiryValue[0]}>{expiryValue[0]}</option>
                }
                else {
                  return <option value={v}>{v}</option>
                }
              })}
            </Form.Control>

            <span className={styles.expiryModalLabel}>Hours</span>
            <Form.Control
                as={"select"}
                onChange={(e) => {
                  const oldExpiry = expiryValue;
                  oldExpiry[1] = parseInt(e.target.value);

                  setExpiryValue(oldExpiry);
                }}>
              {hours.map((v, i) => {
                if (v === -1 && expiryValue[1] === -1) {
                  return <option value={"Hours"}>{"Hours"}</option>
                }
                else if (v === -1 && expiryValue[1] !== -1) {
                  hours.splice(hours.indexOf(expiryValue[1]), 1);
                  return <option value={expiryValue[1]}>{expiryValue[1]}</option>
                }
                else {
                  return <option value={v}>{v}</option>
                }
              })}
            </Form.Control>

            <span className={styles.expiryModalLabel}>Hours</span>
            <Form.Control
                as={"select"}
                onChange={(e) => {
                  const oldExpiry = expiryValue;
                  oldExpiry[2] = parseInt(e.target.value);

                  setExpiryValue(oldExpiry);
                }}>
              {minutes.map((v, i) => {
                if (v === -1 && expiryValue[2] === -1) {
                  return <option value={"Mins"}>{"Mins"}</option>
                }
                else if (v === -1 && expiryValue[2] !== -1) {
                  minutes.splice(minutes.indexOf(expiryValue[2]), 1);
                  return <option value={expiryValue[2]}>{expiryValue[2]}</option>
                }
                else {
                  return <option value={v}>{v}</option>
                }
              })}
            </Form.Control>

          </InputGroup>
        </Modal.Body>
        <Modal.Footer>
          <Button
              variant="info"
              type="submit"
              onClick={handleExpirySubmit}
          >
            Submit
          </Button>
        </Modal.Footer>
      </Modal>

      <Navbar className="justify-content-center">
        <Nav className={styles.optsNavContainer}>
          {actions.map(OptsButton)}
          {opts.map(OptsButton)}
        </Nav>
      </Navbar>
    </div>
  );
}

function OptsButton(obj: {
  title: string;
  content: string;
  icon: JSX.Element;
  callback: () => void;
  hotKey?: string;
  optional?: boolean;
}): JSX.Element {
  return (
    <OverlayTrigger
      key={`opt-${obj.title}`}
      placement={"bottom"}
      overlay={
        <Popover id={`opt-${obj.title}`}>
          <Popover.Title className={styles.popoverHeader} as="h3">
            {obj.title}
            {obj.hotKey && (
              <span
                style={{
                  float: "right",
                  color: "rgba(255, 255, 255, .6)",
                }}
              >
                {obj.hotKey}
              </span>
            )}
          </Popover.Title>
          <Popover.Content>
            {obj.content}{" "}
            {obj.optional !== undefined && (
              <strong>{obj.optional ? "Optional" : "Required"}</strong>
            )}
          </Popover.Content>
        </Popover>
      }
    >
      <div className={styles.optsIconContainer} onClick={() => obj.callback()}>
        {obj.icon}
      </div>
    </OverlayTrigger>
  );
}
