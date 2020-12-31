import { Modal, Nav, Navbar, OverlayTrigger, Popover } from "react-bootstrap";
import React, { useState } from "react";
import EnhancedEncryptionIcon from "@material-ui/icons/EnhancedEncryption";
import HourglassFullIcon from "@material-ui/icons/HourglassFull";
import SaveAltIcon from "@material-ui/icons/SaveAlt";
import EditIcon from "@material-ui/icons/Edit";
import styles from "../styles/OptsBar.module.css";
import { useHotkeys } from "react-hotkeys-hook";

export default function OptsBar() {
  const [showModal, setShowModal] = useState(false);

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
      hotKey: "ctrl+d",
    },
    {
      title: "Create Expiry",
      content: "Create a expiry date for this paste and all its files.",
      optional: true,
      icon: <HourglassFullIcon />,
      callback: () => setShowModal(true),
      hotKey: "ctrl+shift+e",
    },
  ];

  actions.forEach(({ callback, hotKey }) => {
    useHotkeys(hotKey, callback);
  });

  return (
    <div>
      <Modal
        show={showModal}
        onHide={() => setShowModal(false)}
        keyboard={false}
        aria-labelledby="contained-modal-title-vcenter"
        centered
        className={styles.expiryModal}
      >
        <Modal.Header className={styles.expiryModalHeader}>
          <Modal.Title className={styles.expiryModalTitle}>
            Hello World
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>Set EXPIRY BRUH!</Modal.Body>
      </Modal>

      <Navbar className="justify-content-center">
        <Nav className={styles.optsNavContainer}>
          {actions.map((obj) => (
            <OverlayTrigger
              key={`opt-${obj.title}`}
              placement={"bottom"}
              overlay={
                <Popover id={`opt-${obj.title}`}>
                  <Popover.Title className={styles.popoverHeader} as="h3">
                    {obj.title}
                  </Popover.Title>
                  <Popover.Content>{obj.content}</Popover.Content>
                </Popover>
              }
            >
              <div
                className={styles.optsIconContainer}
                onClick={() => obj.callback()}
              >
                {obj.icon}
              </div>
            </OverlayTrigger>
          ))}

          {opts.map((obj) => (
            <OverlayTrigger
              key={`opt-${obj.title}`}
              placement={"bottom"}
              overlay={
                <Popover id={`opt-${obj.title}`}>
                  <Popover.Title className={styles.popoverHeader} as="h3">
                    {obj.title}
                  </Popover.Title>
                  <Popover.Content>
                    {obj.content}
                    <strong> {obj.optional ? "Optional" : "Required"}</strong>
                  </Popover.Content>
                </Popover>
              }
            >
              <div
                className={styles.optsIconContainer}
                onClick={() => obj.callback && obj.callback()}
              >
                {obj.icon}
              </div>
            </OverlayTrigger>
          ))}
        </Nav>
      </Navbar>
    </div>
  );
}
