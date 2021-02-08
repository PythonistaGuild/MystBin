import { useState } from "react";
import { Button, Form, InputGroup, Modal } from "react-bootstrap";
import styles from "../styles/OptsBar.module.css";

export default function ExpiryModal({
  initialValue,
  onHide,
  onSubmit,
}: {
  onHide: () => void;
  initialValue: number[];
  onSubmit: (arg0: number[]) => void;
}) {
  const [expiryValue, setExpiryValue] = useState(initialValue);
  let days = [-1];
  let hours = [-1];
  const minutes = [-1, 0, 5, 15, 30, 45];

  for (let i = 0; i <= 31; i++) {
    days.push(i);
  }

  for (let i = 0; i <= 23; i++) {
    hours.push(i);
  }

  const handleExpirySubmit = (e) => {
    e.preventDefault();
    onHide();
    onSubmit(expiryValue);
  };

  let optionMap = {
    Days: [0, days],
    Hours: [1, hours],
    Mins: [2, minutes],
  };

  return (
    <Modal
      show={true}
      onHide={onHide}
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
        <Form
          inline
          style={{
            justifyContent: "center",
          }}
          onSubmit={handleExpirySubmit}
        >
          {Object.keys(optionMap).map((optName) => {
            let [index, options]: [number, number[]] = optionMap[optName];

            return (
              <>
                <Form.Label className="my-1 mr-2" htmlFor={`expiry-${optName}`}>
                  {optName}
                </Form.Label>
                <Form.Control
                  id={`expiry-${optName}`}
                  className="my-1 mr-sm-2"
                  as={"select"}
                  custom
                  onChange={(e) => {
                    const oldExpiry = expiryValue;
                    oldExpiry[index] = parseInt(e.target.value);

                    setExpiryValue(oldExpiry);
                  }}
                >
                  {options.map((v) => {
                    let chosen = expiryValue[index];
                    return (
                      <option value={v} selected={chosen === v}>
                        {v === -1 ? optName : v}
                      </option>
                    );
                  })}
                </Form.Control>
              </>
            );
          })}
        </Form>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="info" type="submit" onClick={handleExpirySubmit}>
          Submit
        </Button>
      </Modal.Footer>
    </Modal>
  );
}
