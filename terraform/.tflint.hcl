plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

plugin "yandex" {
  enabled = true
}

config {
  module = true
  force  = false
}

